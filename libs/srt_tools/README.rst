srt_tools contains utilities written to process SRT files. All utilities use
the Python srt_ library internally.

.. _srt: https://github.com/cdown/srt

Usage
-----

You can call ``srt`` directly to see a list of all available utilities.

.. code::

    srt [utility-name] [args ...]

Arbitrary things can be done with *srt process* and *srt lines-matching*, for
example:

.. code::

    # Strip HTML
    srt process -m re -f 'lambda sub: re.sub("<[^<]+?>", "", sub)'

    # Only keep Chinese subtitles
    srt lines-matching -m hanzidentifier -f hanzidentifier.has_chinese

Utilities
---------

- *deduplicate* removes subtitles with duplicate content. If you have subtitles
  which mistakenly repeat the same content in different subs at roughly the
  same time, you can run this tool to remove them.
- *fixed-timeshift* does fixed time correction. For example, if you have a
  movie that is consistently out of sync by two seconds, you can run this tool
  to shift the entire subtitle two seconds ahead or behind.
- *linear-timeshift* does linear time correction. If you have a movie that
  runs slower or faster than the subtitle that you have, it will repeatedly
  lose sync. This tool can apply linear time corrections to all subtitles in
  the SRT, resyncing it with the video.
- *lines-matching* takes a function and removes lines that don't return true
  when passed to it. For example, you can keep only lines that contain Chinese
  by installing the hanzidentifier_ package, and running
  ``srt lines-matching -m hanzidentifier -f hanzidentifier.has_chinese < input``.
- *mux* can mux_ multiple subtitles together into one. For example, if you
  have a Chinese subtitle and an English subtitle, and you want to have one
  subtitle file that contains both, this tool can do that for you. It also
  supports clamping subtitles starting or ending at similar times to the same
  time to avoid subtitles jumping around the screen.
- *normalise* standardises and cleans up SRT files. For example, it removes
  spurious newlines, normalises timestamps, and fixes subtitle indexing to a
  format that all media players should accept, with no noncompliant data.
- *play* plays subtitles in the terminal at the time they are scheduled to
  display (note: it does not clear them from the screen afterwards). If you
  need to fast-forward to some point, you can combine it with
  *fixed-timeshift*.
- *process* allows processing text freely. It takes a function, similarly to
  *lines-matching*, and changes SRT content into the return value. For example,
  you can naively strip some basic HTML-like markup with
  ``srt process -m re -f 'lambda sub: re.sub("<[^<]+?>", "", sub)'``. HTML-like
  syntax is especially prevalant in `SSA/ASS`_ subtitles that have been
  directly converted to SRT.

.. _mux: https://en.wikipedia.org/wiki/Multiplexing
.. _`SSA/ASS`: https://en.wikipedia.org/wiki/SubStation_Alpha
.. _hanzidentifier: https://github.com/tsroten/hanzidentifier
