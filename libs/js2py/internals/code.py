from opcodes import *
from space import *
from base import *


class Code:
    '''Can generate, store and run sequence of ops representing js code'''

    def __init__(self, is_strict=False):
        self.tape = []
        self.compiled = False
        self.label_locs = None
        self.is_strict = is_strict

        self.contexts = []
        self.current_ctx = None
        self.return_locs = []
        self._label_count = 0
        self.label_locs = None

        # useful references
        self.GLOBAL_THIS = None
        self.space = None

    def get_new_label(self):
        self._label_count += 1
        return self._label_count

    def emit(self, op_code, *args):
        ''' Adds op_code with specified args to tape '''
        self.tape.append(OP_CODES[op_code](*args))

    def compile(self, start_loc=0):
        ''' Records locations of labels and compiles the code '''
        self.label_locs = {} if self.label_locs is None else self.label_locs
        loc = start_loc
        while loc < len(self.tape):
            if type(self.tape[loc]) == LABEL:
                self.label_locs[self.tape[loc].num] = loc
                del self.tape[loc]
                continue
            loc += 1
        self.compiled = True

    def _call(self, func, this, args):
        ''' Calls a bytecode function func
            NOTE:  use !ONLY! when calling functions from native methods! '''
        assert not func.is_native
        # fake call - the the runner to return to the end of the file
        old_contexts = self.contexts
        old_return_locs = self.return_locs
        old_curr_ctx = self.current_ctx

        self.contexts = [FakeCtx()]
        self.return_locs = [len(self.tape)]  # target line after return

        # prepare my ctx
        my_ctx = func._generate_my_context(this, args)
        self.current_ctx = my_ctx

        # execute dunction
        ret = self.run(my_ctx, starting_loc=self.label_locs[func.code])

        # bring back old execution
        self.current_ctx = old_curr_ctx
        self.contexts = old_contexts
        self.return_locs = old_return_locs

        return ret

    def execute_fragment_under_context(self, ctx, start_label, end_label):
        ''' just like run but returns if moved outside of the specified fragment
            # 4 different exectution results
            # 0=normal, 1=return, 2=jump_outside, 3=errors
            # execute_fragment_under_context returns:
            # (return_value, typ, return_value/jump_loc/py_error)
            # ctx.stack must be len 1 and its always empty after the call.
        '''
        old_curr_ctx = self.current_ctx
        try:
            self.current_ctx = ctx
            return self._execute_fragment_under_context(
                ctx, start_label, end_label)
        except JsException as err:
            # undo the things that were put on the stack (if any)
            # don't worry, I know the recovery is possible through try statement and for this reason try statement
            # has its own context and stack so it will not delete the contents of the outer stack
            del ctx.stack[:]
            return undefined, 3, err
        finally:
            self.current_ctx = old_curr_ctx

    def _execute_fragment_under_context(self, ctx, start_label, end_label):
        start, end = self.label_locs[start_label], self.label_locs[end_label]
        initial_len = len(ctx.stack)
        loc = start
        entry_level = len(self.contexts)
        # for e in self.tape[start:end]:
        #     print e

        while loc < len(self.tape):
            #print loc, self.tape[loc]
            if len(self.contexts) == entry_level and loc >= end:
                assert loc == end
                assert len(ctx.stack) == (
                    1 + initial_len), 'Stack change must be equal to +1!'
                return ctx.stack.pop(), 0, None  # means normal return

            # execute instruction
            status = self.tape[loc].eval(ctx)

            # check status for special actions
            if status is not None:
                if type(status) == int:  # jump to label
                    loc = self.label_locs[status]
                    if len(self.contexts) == entry_level:
                        # check if jumped outside of the fragment and break if so
                        if not start <= loc < end:
                            assert len(ctx.stack) == (
                                1 + initial_len
                            ), 'Stack change must be equal to +1!'
                            return ctx.stack.pop(), 2, status  # jump outside
                    continue

                elif len(status) == 2:  # a call or a return!
                    # call: (new_ctx, func_loc_label_num)
                    if status[0] is not None:
                        # append old state to the stack
                        self.contexts.append(ctx)
                        self.return_locs.append(loc + 1)
                        # set new state
                        loc = self.label_locs[status[1]]
                        ctx = status[0]
                        self.current_ctx = ctx
                        continue

                    # return: (None, None)
                    else:
                        if len(self.contexts) == entry_level:
                            assert len(ctx.stack) == 1 + initial_len
                            return undefined, 1, ctx.stack.pop(
                            )  # return signal
                        return_value = ctx.stack.pop()
                        ctx = self.contexts.pop()
                        self.current_ctx = ctx
                        ctx.stack.append(return_value)

                        loc = self.return_locs.pop()
                        continue
            # next instruction
            loc += 1
        assert False, 'Remember to add NOP at the end!'

    def run(self, ctx, starting_loc=0):
        loc = starting_loc
        self.current_ctx = ctx
        while loc < len(self.tape):
            # execute instruction
            #print loc, self.tape[loc]
            status = self.tape[loc].eval(ctx)

            # check status for special actions
            if status is not None:
                if type(status) == int:  # jump to label
                    loc = self.label_locs[status]
                    continue

                elif len(status) == 2:  # a call or a return!
                    # call: (new_ctx, func_loc_label_num)
                    if status[0] is not None:
                        # append old state to the stack
                        self.contexts.append(ctx)
                        self.return_locs.append(loc + 1)
                        # set new state
                        loc = self.label_locs[status[1]]
                        ctx = status[0]
                        self.current_ctx = ctx
                        continue

                    # return: (None, None)
                    else:
                        return_value = ctx.stack.pop()
                        ctx = self.contexts.pop()
                        self.current_ctx = ctx
                        ctx.stack.append(return_value)

                        loc = self.return_locs.pop()
                        continue
            # next instruction
            loc += 1
        assert len(ctx.stack) == 1, ctx.stack
        return ctx.stack.pop()


class FakeCtx(object):
    def __init__(self):
        self.stack = []
