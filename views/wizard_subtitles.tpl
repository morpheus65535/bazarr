                <div class="ui dividing header">Subtitles options</div>
                <div class="twelve wide column">
                    <div class="ui grid">

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subtitle Folder</label>
                            </div>
                            <div class="five wide column">
                                <select name="settings_subfolder" id="settings_subfolder"
                                        class="ui fluid selection dropdown">
                                    <option value="current">Alongside Media File</option>
                                    <option value="relative">Relative Path To Media File</option>
                                    <option value="absolute">Absolute Path</option>
                                </select>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon"
                                     data-tooltip='Choose the folder you want to store/read the Subtitles in'
                                     data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row subfolder">
                            <div class="two wide column"></div>
                            <div class="right aligned four wide column">
                                <label>Custom Subtitle Folder</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_subfolder_custom" name="settings_subfolder_custom"
                                               type="text" value="{{ settings.general.subfolder_custom }}">
                                    </div>
                                </div>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon"
                                     data-tooltip='Choose your own folder for Subtitles' data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Use Embedded Subtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_embedded" class="ui toggle checkbox"
                                     data-embedded={{ settings.general.getboolean('use_embedded_subs') }}>
                                    <input name="settings_general_embedded" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon"
                                         data-tooltip="Use Embedded Subtitles in media files when determining missing ones."
                                         data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>

                % include('providers.tpl')

                <div class="ui dividing header">Subtitles languages</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Single Language</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_single_language" class="ui toggle checkbox"  data-single-language={{settings.general.getboolean('single_language')}}>
                                    <input name="settings_general_single_language" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Download a single subtitle file without adding the language code to the filename." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Enabled Languages</label>
                            </div>
                            <div class="eleven wide column">
                                <div class='field'>
                                    <select name="settings_subliminal_languages" id="settings_languages" multiple="" class="ui fluid search selection dropdown">
                                        <option value="">Languages</option>
                                        %enabled_languages = []
                                        %for language in settings_languages:
                                        <option value="{{language['code2']}}">{{language['name']}}</option>
                                        %if language['enabled'] == True:
                                        %	enabled_languages.append(str(language['code2']))
                                        %end
                                        %end
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ui dividing header">Series default settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Default Enabled</label>
                            </div>
                            <div class="one wide column">
                                <div class="nine wide column">
                                    <div id="settings_serie_default_enabled_div" class="ui toggle checkbox">
                                        <input name="settings_serie_default_enabled" id="settings_serie_default_enabled" type="checkbox">
                                        <label></label>
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Apply only to Series added to Bazarr after enabling this option." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Languages</label>
                            </div>
                            <div class="eleven wide column">
                                <div class='field'>
                                    <select name="settings_serie_default_languages" id="settings_serie_default_languages" multiple="" class="ui fluid search selection dropdown">
                                        %if not settings.general.getboolean('single_language'):
                                        <option value="">Languages</option>
                                        %else:
                                        <option value="None">None</option>
                                        %end
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Hearing-Impaired</label>
                            </div>
                            <div class="eleven wide column">
                                <div class="nine wide column">
                                    <div id="settings_serie_default_hi_div" class="ui toggle checkbox">
                                        <input name="settings_serie_default_hi" id="settings_serie_default_hi" type="checkbox">
                                        <label></label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Forced</label>
                            </div>
                            <div class="eleven wide column">
                                <div class='field'>
                                    <select name="settings_serie_default_forced" id="settings_serie_default_forced" class="ui fluid selection dropdown">
                                        <option value="False">False</option>
                                        <option value="True">True</option>
                                        <option value="Both">Both</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ui dividing header">Movie Default Settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Default Enabled</label>
                            </div>
                            <div class="one wide column">
                                <div class="nine wide column">
                                    <div id="settings_movie_default_enabled_div" class="ui toggle checkbox">
                                        <input name="settings_movie_default_enabled" id="settings_movie_default_enabled" type="checkbox">
                                        <label></label>
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Apply only to Movies added to Bazarr after enabling this option." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div id="movie_default_languages_label" class="right aligned four wide column">
                                <label>Languages</label>
                            </div>
                            <div class="eleven wide column">
                                <div class='field'>
                                    <select name="settings_movie_default_languages" id="settings_movie_default_languages" multiple="" class="ui fluid search selection dropdown">
                                        %if not settings.general.getboolean('single_language'):
                                        <option value="">Languages</option>
                                        %else:
                                        <option value="None">None</option>
                                        %end
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div id="movie_default_hi_label" class="right aligned four wide column">
                                <label>Hearing-Impaired</label>
                            </div>
                            <div class="eleven wide column">
                                <div class="nine wide column">
                                    <div id="settings_movie_default_hi_div" class="ui toggle checkbox">
                                        <input name="settings_movie_default_hi" id="settings_movie_default_hi" type="checkbox">
                                        <label></label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div id="movie_default_forced_label" class="right aligned four wide column">
                                <label>Forced</label>
                            </div>
                            <div class="eleven wide column">
                                <div class='field'>
                                    <select name="settings_movie_default_forced" id="settings_movie_default_forced" class="ui fluid selection dropdown">
                                        <option value="False">False</option>
                                        <option value="True">True</option>
                                        <option value="Both">Both</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                    if ($('#settings_embedded').data("embedded") === "True") {
                        $("#settings_embedded").checkbox('check');
                    } else {
                        $("#settings_embedded").checkbox('uncheck');
                    }

                    if ($('#settings_single_language').data("single-language") === "True") {
                        $("#settings_single_language").checkbox('check');
                    } else {
                        $("#settings_single_language").checkbox('uncheck');
                    }

                    $('#settings_languages').dropdown('setting', 'onAdd', function(val, txt){
                        $("#settings_serie_default_languages").append(
                            $("<option></option>").attr("value", val).text(txt)
                        );
                        $("#settings_movie_default_languages").append(
                            $("<option></option>").attr("value", val).text(txt)
                        )
                    });

                    $('#settings_languages').dropdown('setting', 'onRemove', function(val){
                        $("#settings_serie_default_languages").dropdown('remove selected', val);
                        $("#settings_serie_default_languages option[value='" + val + "']").remove();

                        $("#settings_movie_default_languages").dropdown('remove selected', val);
                        $("#settings_movie_default_languages option[value='" + val + "']").remove();
                    });

                    if ($('#settings_serie_default_enabled_div').data("enabled") === "True") {
                        $("#settings_serie_default_enabled_div").checkbox('check');
                    } else {
                        $("#settings_serie_default_enabled_div").checkbox('uncheck');
                    }

                    if ($('#settings_serie_default_enabled_div').data("enabled") === "True") {
                        $("#settings_serie_default_languages").removeClass('disabled');
                        $("#settings_serie_default_hi_div").removeClass('disabled');
                        $("#settings_serie_default_forced_div").removeClass('disabled');
                    } else {
                        $("#settings_serie_default_languages").addClass('disabled');
                        $("#settings_serie_default_hi_div").addClass('disabled');
                        $("#settings_serie_default_forced_div").addClass('disabled');
                    }

                    $('#settings_serie_default_enabled_div').checkbox({
                        onChecked: function() {
                            $("#settings_serie_default_languages").parent().removeClass('disabled');
                            $("#settings_serie_default_hi_div").removeClass('disabled');
                            $("#settings_serie_default_forced").parent().removeClass('disabled');
                        },
                        onUnchecked: function() {
                            $("#settings_serie_default_languages").parent().addClass('disabled');
                            $("#settings_serie_default_hi_div").addClass('disabled');
                            $("#settings_serie_default_forced").parent().addClass('disabled');
                        }
                    });

                    if ($('#settings_serie_default_hi_div').data("hi") === "True") {
                        $("#settings_serie_default_hi_div").checkbox('check');
                    } else {
                        $("#settings_serie_default_hi_div").checkbox('uncheck');
                    }

                    if ($('#settings_movie_default_enabled_div').data("enabled") === "True") {
                        $("#settings_movie_default_enabled_div").checkbox('check');
                    } else {
                        $("#settings_movie_default_enabled_div").checkbox('uncheck');
                    }

                    if ($('#settings_movie_default_enabled_div').data("enabled") === "True") {
                        $("#settings_movie_default_languages").removeClass('disabled');
                        $("#settings_movie_default_hi_div").removeClass('disabled');
                        $("#settings_movie_default_forced_div").removeClass('disabled');
                    } else {
                        $("#settings_movie_default_languages").addClass('disabled');
                        $("#settings_movie_default_hi_div").addClass('disabled');
                        $("#settings_movie_default_forced_div").addClass('disabled');
                    }

                    $('#settings_movie_default_enabled_div').checkbox({
                        onChecked: function() {
                            $("#settings_movie_default_languages").parent().removeClass('disabled');
                            $("#settings_movie_default_hi_div").removeClass('disabled');
                            $("#settings_movie_default_forced").parent().removeClass('disabled');
                        },
                        onUnchecked: function() {
                            $("#settings_movie_default_languages").parent().addClass('disabled');
                            $("#settings_movie_default_hi_div").addClass('disabled');
                            $("#settings_movie_default_forced").parent().addClass('disabled');
                        }
                    });

                    if ($('#settings_movie_default_hi_div').data("hi") === "True") {
                        $("#settings_movie_default_hi_div").checkbox('check');
                    } else {
                        $("#settings_movie_default_hi_div").checkbox('uncheck');
                    }

                    if ($("#settings_single_language").checkbox('is checked')) {
                        $("#settings_serie_default_languages").parent().removeClass('multiple');
                        $("#settings_serie_default_languages").removeAttr('multiple');
                        $("#settings_movie_default_languages").parent().removeClass('multiple');
                        $("#settings_movie_default_languages").removeAttr('multiple');
                    } else {
                        $("#settings_serie_default_languages").parent().addClass('multiple');
                        $("#settings_serie_default_languages").attr('multiple');
                        $("#settings_movie_default_languages").parent().addClass('multiple');
                        $("#settings_movie_default_languages").attr('multiple');
                    }

                    $("#settings_single_language").on('change', function() {
                        if ($("#settings_single_language").checkbox('is checked')) {
                            $("#settings_serie_default_languages").dropdown('clear');
                            $("#settings_movie_default_languages").dropdown('clear');
                            $("#settings_serie_default_languages").prepend("<option value='None' selected='selected'>None</option>");
                            $("#settings_movie_default_languages").prepend("<option value='None' selected='selected'>None</option>");
                            $("#settings_serie_default_languages").parent().removeClass('multiple');
                            $("#settings_serie_default_languages").removeAttr('multiple');
                            $("#settings_movie_default_languages").parent().removeClass('multiple');
                            $("#settings_movie_default_languages").removeAttr('multiple');
                        } else {
                            $("#settings_serie_default_languages").dropdown('clear');
                            $("#settings_movie_default_languages").dropdown('clear');
                            $("#settings_serie_default_languages option[value='None']").remove();
                            $("#settings_movie_default_languages option[value='None']").remove();
                            $("#settings_serie_default_languages").parent().addClass('multiple');
                            $("#settings_serie_default_languages").attr('multiple');
                            $("#settings_movie_default_languages").parent().addClass('multiple');
                            $("#settings_movie_default_languages").attr('multiple');
                        }
                    });

                    $('#settings_languages').dropdown('clear');
                    $('#settings_languages').dropdown('set selected',{{!enabled_languages}});
                    $('#settings_subfolder').dropdown('clear');
                    $('#settings_subfolder').dropdown('set selected', '{{!settings.general.subfolder}}');

                    %if settings.general.serie_default_language != 'None':
                    $('#settings_serie_default_languages').dropdown('set selected',{{!settings.general.serie_default_language}});
                    %end
                    %if settings.general.movie_default_language != 'None':
                    $('#settings_movie_default_languages').dropdown('set selected',{{!settings.general.movie_default_language}});
                    %end

                    $('#settings_serie_default_forced').dropdown('set selected','{{!settings.general.serie_default_forced}}');
                    $('#settings_movie_default_forced').dropdown('set selected','{{!settings.general.movie_default_forced}}');

                    $('#settings_languages').dropdown('setting', 'onChange', function(){
                        $('.form').form('validate field', 'settings_subliminal_languages');
                    });

                    if (($('#settings_subfolder').val() !== "relative") && ($('#settings_subfolder').val() !== "absolute")) {
                        $('.subfolder').hide();
                    }

                    $('#settings_subfolder').dropdown('setting', 'onChange', function(){
                        if (($('#settings_subfolder').val() !== "relative") && ($('#settings_subfolder').val() !== "absolute")) {
                            $('.subfolder').hide();
                        } else {
                            $('.subfolder').show();
                        }
                    });
                </script>
