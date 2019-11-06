# Copyright (c) 2014 Palantir Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Thread safe sqlite3 interface."""

__author__ = "Shawn Lee"
__email__ = "shawnl@palantir.com"
__license__ = "MIT"

import logging
try:
    import queue as Queue # module re-named in Python 3
except ImportError:
    import Queue
import sqlite3
import threading
import time
import uuid

LOGGER = logging.getLogger('sqlite3worker')


class Sqlite3Worker(threading.Thread):
    """Sqlite thread safe object.

    Example:
        from sqlite3worker import Sqlite3Worker
        sql_worker = Sqlite3Worker("/tmp/test.sqlite")
        sql_worker.execute(
            "CREATE TABLE tester (timestamp DATETIME, uuid TEXT)")
        sql_worker.execute(
            "INSERT into tester values (?, ?)", ("2010-01-01 13:00:00", "bow"))
        sql_worker.execute(
            "INSERT into tester values (?, ?)", ("2011-02-02 14:14:14", "dog"))
        sql_worker.execute("SELECT * from tester")
        sql_worker.close()
    """
    def __init__(self, file_name, max_queue_size=100, as_dict=False):
        """Automatically starts the thread.

        Args:
            file_name: The name of the file.
            max_queue_size: The max queries that will be queued.
            as_dict: Return result as a dictionary.
        """
        threading.Thread.__init__(self)
        self.daemon = True
        self.sqlite3_conn = sqlite3.connect(
            file_name, check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES)
        if as_dict:
            self.sqlite3_conn.row_factory = dict_factory
        self.sqlite3_cursor = self.sqlite3_conn.cursor()
        self.sql_queue = Queue.Queue(maxsize=max_queue_size)
        self.results = {}
        self.max_queue_size = max_queue_size
        self.exit_set = False
        # Token that is put into queue when close() is called.
        self.exit_token = str(uuid.uuid4())
        self.start()
        self.thread_running = True

    def run(self):
        """Thread loop.

        This is an infinite loop.  The iter method calls self.sql_queue.get()
        which blocks if there are not values in the queue.  As soon as values
        are placed into the queue the process will continue.

        If many executes happen at once it will churn through them all before
        calling commit() to speed things up by reducing the number of times
        commit is called.
        """
        LOGGER.debug("run: Thread started")
        execute_count = 0
        for token, query, values, only_one in iter(self.sql_queue.get, None):
            LOGGER.debug("sql_queue: %s", self.sql_queue.qsize())
            if token != self.exit_token:
                LOGGER.debug("run: %s, %s", query, values)
                self.run_query(token, query, values, only_one)
                execute_count += 1
                # Let the executes build up a little before committing to disk
                # to speed things up.
                if (
                        self.sql_queue.empty() or
                        execute_count == self.max_queue_size):
                    LOGGER.debug("run: commit")
                    self.sqlite3_conn.commit()
                    execute_count = 0
            # Only exit if the queue is empty. Otherwise keep getting
            # through the queue until it's empty.
            if self.exit_set and self.sql_queue.empty():
                self.sqlite3_conn.commit()
                self.sqlite3_conn.close()
                self.thread_running = False
                return

    def run_query(self, token, query, values, only_one):
        """Run a query.

        Args:
            token: A uuid object of the query you want returned.
            query: A sql query with ? placeholders for values.
            values: A tuple of values to replace "?" in query.
        """
        if query.lower().strip().startswith("select"):
            try:
                self.sqlite3_cursor.execute(query, values)
                if only_one:
                    self.results[token] = self.sqlite3_cursor.fetchone()
                else:
                    self.results[token] = self.sqlite3_cursor.fetchall()
            except sqlite3.Error as err:
                # Put the error into the output queue since a response
                # is required.
                self.results[token] = (
                    "Query returned error: %s: %s: %s" % (query, values, err))
                LOGGER.error(
                    "Query returned error: %s: %s: %s", query, values, err)
        else:
            try:
                self.sqlite3_cursor.execute(query, values)
                if query.lower().strip().startswith(("insert", "update")):
                    self.results[token] = self.sqlite3_cursor.rowcount
            except sqlite3.Error as err:
                self.results[token] = (
                        "Query returned error: %s: %s: %s" % (query, values, err))
                LOGGER.error(
                    "Query returned error: %s: %s: %s", query, values, err)

    def close(self):
        """Close down the thread and close the sqlite3 database file."""
        self.exit_set = True
        self.sql_queue.put((self.exit_token, "", "", ""), timeout=5)
        # Sleep and check that the thread is done before returning.
        while self.thread_running:
            time.sleep(.01)  # Don't kill the CPU waiting.

    @property
    def queue_size(self):
        """Return the queue size."""
        return self.sql_queue.qsize()

    def query_results(self, token):
        """Get the query results for a specific token.

        Args:
            token: A uuid object of the query you want returned.

        Returns:
            Return the results of the query when it's executed by the thread.
        """
        delay = .001
        while True:
            if token in self.results:
                return_val = self.results[token]
                del self.results[token]
                return return_val
            # Double back on the delay to a max of 8 seconds.  This prevents
            # a long lived select statement from trashing the CPU with this
            # infinite loop as it's waiting for the query results.
            LOGGER.debug("Sleeping: %s %s", delay, token)
            time.sleep(delay)
            if delay < 8:
                delay += delay

    def execute(self, query, values=None, only_one=False):
        """Execute a query.

        Args:
            query: The sql string using ? for placeholders of dynamic values.
            values: A tuple of values to be replaced into the ? of the query.

        Returns:
            If it's a select query it will return the results of the query.
        """
        if self.exit_set:
            LOGGER.debug("Exit set, not running: %s, %s", query, values)
            return "Exit Called"
        LOGGER.debug("execute: %s, %s", query, values)
        values = values or []
        # A token to track this query with.
        token = str(uuid.uuid4())
        # If it's a select we queue it up with a token to mark the results
        # into the output queue so we know what results are ours.
        if query.lower().strip().startswith(("select", "insert", "update")):
            self.sql_queue.put((token, query, values, only_one), timeout=5)
            return self.query_results(token)
        else:
            self.sql_queue.put((token, query, values, only_one), timeout=5)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
