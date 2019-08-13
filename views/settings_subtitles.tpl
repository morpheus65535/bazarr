                <div class="ui dividing header">Subtitles options</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Use scene name when available</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_scenename" class="ui toggle checkbox" data-scenename={{settings.general.getboolean('use_scenename')}}>
                                    <input name="settings_general_scenename" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Use the scene name from Sonarr/Radarr if available to circumvent usage of episode file renaming." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Use MediaInfo</label>
                            </div>
                            <div class="one wide column">
                                % import platform
                                <div id="settings_mediainfo" class="ui toggle checkbox{{' disabled' if platform.system() == 'Linux' else ''}}" data-mediainfo={{settings.general.getboolean('use_mediainfo')}}>
                                    <input name="settings_general_mediainfo" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Use MediaInfo to extract video and audio stream properties." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="This settings is only available on Windows and MacOS." data-inverted="">
                                        <i class="yellow warning sign icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Minimum score for episodes</label>
                            </div>
                            <div class="two wide column">
                                <div class='field'>
                                    <div class="ui input">
                                        <input name="settings_general_minimum_score" type="number" min="0" max="100" step="1" onkeydown="return false" value="{{settings.general.minimum_score}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Minimum score for an episode subtitle to be downloaded (0 to 100)." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Minimum score for movies</label>
                            </div>
                            <div class="two wide column">
                                <div class='field'>
                                    <div class="ui input">
                                        <input name="settings_general_minimum_score_movies" type="number" min="0" max="100" step="1" onkeydown="return false" value="{{settings.general.minimum_score_movie}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Minimum score for a movie subtitle to be downloaded (0 to 100)." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subtitle folder</label>
                            </div>
                            <div class="five wide column">
                                <select name="settings_subfolder" id="settings_subfolder"
                                        class="ui fluid selection dropdown">
                                    <option value="current">Alongside media file</option>
                                    <option value="relative">Relative path to media file</option>
                                    <option value="absolute">Absolute path</option>
                                </select>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon"
                                     data-tooltip='Choose folder where you want to store/read the subtitles'
                                     data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row subfolder">
                            <div class="two wide column"></div>
                            <div class="right aligned four wide column">
                                <label>Custom Subtitle folder</label>
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
                                     data-tooltip='Choose your own folder for the subtitles' data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Upgrade previously downloaded subtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_upgrade_subs" class="ui toggle checkbox" data-upgrade={{settings.general.getboolean('upgrade_subs')}}>
                                    <input name="settings_upgrade_subs" type="checkbox">
                                    <label></label>
                                </div>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon"
                                     data-tooltip='Schedule a task that run every 12 hours to upgrade subtitles previously downloaded by Bazarr.'
                                     data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row upgrade_subs">
                            <div class="two wide column"></div>
                            <div class="right aligned four wide column">
                                <label>Number of days to go back in history to upgrade subtitles (up to 30)</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_days_to_upgrade_subs" name="settings_days_to_upgrade_subs"
                                               type="text" value="{{ settings.general.days_to_upgrade_subs }}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row upgrade_subs">
                            <div class="two wide column"></div>
                            <div class="right aligned four wide column">
                                <label>Upgrade manually downloaded subtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_upgrade_manual" class="ui toggle checkbox" data-upgrade-manual={{settings.general.getboolean('upgrade_manual')}}>
                                    <input name="settings_upgrade_manual" type="checkbox">
                                    <label></label>
                                </div>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon"
                                     data-tooltip='Enable or disable upgrade of manually searched and downloaded subtitles.'
                                     data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Use embedded subtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_embedded" class="ui toggle checkbox" data-embedded={{settings.general.getboolean('use_embedded_subs')}}>
                                    <input name="settings_general_embedded" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Use embedded subtitles in media files when determining missing ones." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Ignore embedded PGS subtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_ignore_pgs" class="ui toggle checkbox" data-ignorepgs={{settings.general.getboolean('ignore_pgs_subs')}}>
                                    <input name="settings_general_ignore_pgs" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Ignores pgs subtitles in embedded subtitles detection. Only relevant if 'Use embedded subtitles' is enabled." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Adaptive searching</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_adaptive_searching" class="ui toggle checkbox" data-adaptive={{settings.general.getboolean('adaptive_searching')}}>
                                    <input name="settings_general_adaptive_searching" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="When searching for subtitles, Bazarr will search less frequently after sometime to limit call to providers." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Search enabled providers simultaneously</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_multithreading" class="ui toggle checkbox"
                                     data-multithreading={{ settings.general.getboolean('multithreading') }}>
                                    <input name="settings_general_multithreading" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Search multi providers at once (Don't choose this on low powered devices)" data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Encode subtitles to UTF8</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_utf8_encode" class="ui toggle checkbox" data-utf8encode={{ settings.general.getboolean('utf8_encode') }}>
                                    <input name="settings_general_utf8_encode" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Re-encode downloaded subtitles to UTF8. Should be left enabled in most case." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ui dividing header">Anti-captcha options</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Provider</label>
                            </div>
                            <div class="five wide column">
                                <select name="settings_anti_captcha_provider" id="settings_anti_captcha_provider" class="ui fluid selection dropdown">
                                    <option value="None">None</option>
                                    <option value="anti-captcha">Anti-Captcha</option>
                                    <option value="death-by-captcha">Death by Captcha</option>
                                </select>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon"
                                     data-tooltip='Choose the anti-captcha provider you want to use.'
                                     data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row anticaptcha">
                            <div class="two wide column"></div>
                            <div class="right aligned four wide column">
                                <label>Provider website</label>
                            </div>
                            <div class="five wide column">
                                <a href="http://getcaptchasolution.com/eixxo1rsnw" target="_blank">Anti-Captcha.com</a>
                            </div>
                        </div>

                        <div class="middle aligned row anticaptcha">
                            <div class="two wide column"></div>
                            <div class="right aligned four wide column">
                                <label>Account Key</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_anti_captcha_key" name="settings_anti_captcha_key"
                                               type="text" value="{{ settings.anticaptcha.anti_captcha_key }}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row deathbycaptcha">
                            <div class="two wide column"></div>
                            <div class="right aligned four wide column">
                                <label>Provider website</label>
                            </div>
                            <div class="five wide column">
                                <a href="https://www.deathbycaptcha.com" target="_blank">DeathByCaptcha.com</a>
                            </div>
                        </div>

                        <div class="middle aligned row deathbycaptcha">
                            <div class="two wide column"></div>
                            <div class="right aligned four wide column">
                                <label>Username</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_death_by_captcha_username" name="settings_death_by_captcha_username"
                                               type="text" value="{{ settings.deathbycaptcha.username }}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row deathbycaptcha">
                            <div class="two wide column"></div>
                            <div class="right aligned four wide column">
                                <label>Password</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_death_by_captcha_password" name="settings_death_by_captcha_password"
                                               type="password" value="{{ settings.deathbycaptcha.password }}">
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
                                <label>Single language</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_single_language" class="ui toggle checkbox" data-single-language={{settings.general.getboolean('single_language')}}>
                                    <input name="settings_general_single_language" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Download a single subtitles file and don't add the language code to the filename." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Enabled languages</label>
                            </div>
                            <div class="eleven wide column">
                                <div class='field'>
                                    <select name="settings_subliminal_languages" id="settings_languages" multiple="" class="ui fluid search selection dropdown">
                                        <option value="">Languages</option>
                                        %enabled_languages = []
                                        %for language in settings_languages:
                                        <option value="{{language[1]}}">{{language[2]}}</option>
                                        %if language[3] == True:
                                        %	enabled_languages.append(str(language[1]))
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
                                <label>Default enabled</label>
                            </div>
                            <div class="one wide column">
                                <div class="nine wide column">
                                    <div id="settings_serie_default_enabled_div" class="ui toggle checkbox" data-enabled="{{settings.general.getboolean('serie_default_enabled')}}">
                                        <input name="settings_serie_default_enabled" id="settings_serie_default_enabled" type="checkbox">
                                        <label></label>
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Apply only to series added to Bazarr after enabling this option." data-inverted="">
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
                                        %if settings.general.getboolean('single_language') is False:
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
                                <label>Hearing-impaired</label>
                            </div>
                            <div class="eleven wide column">
                                <div class="nine wide column">
                                    <div id="settings_serie_default_hi_div" class="ui toggle checkbox" data-hi="{{settings.general.getboolean('serie_default_hi')}}">
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

                <div class="ui dividing header">Movies default settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Default enabled</label>
                            </div>
                            <div class="one wide column">
                                <div class="nine wide column">
                                    <div id="settings_movie_default_enabled_div" class="ui toggle checkbox" data-enabled="{{settings.general.getboolean('movie_default_enabled')}}">
                                        <input name="settings_movie_default_enabled" id="settings_movie_default_enabled" type="checkbox">
                                        <label></label>
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Apply only to movies added to Bazarr after enabling this option." data-inverted="">
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
                                        %if settings.general.getboolean('single_language') is False:
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
                                <label>Hearing-impaired</label>
                            </div>
                            <div class="eleven wide column">
                                <div class="nine wide column">
                                    <div id="settings_movie_default_hi_div" class="ui toggle checkbox" data-hi="{{settings.general.getboolean('movie_default_hi')}}">
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
                    if ($('#settings_single_language').data("single-language") === "True") {
                        $("#settings_single_language").checkbox('check');
                    } else {
                        $("#settings_single_language").checkbox('uncheck');
                    }

                    if ($('#settings_scenename').data("scenename") === "True") {
                        $("#settings_scenename").checkbox('check');
                    } else {
                        $("#settings_scenename").checkbox('uncheck');
                    }

                    if ($('#settings_mediainfo').data("mediainfo") === "True") {
                        $("#settings_mediainfo").checkbox('check');
                    } else {
                        $("#settings_mediainfo").checkbox('uncheck');
                    }

                    if ($('#settings_upgrade_subs').data("upgrade") === "True") {
                        $("#settings_upgrade_subs").checkbox('check');
                    } else {
                        $("#settings_upgrade_subs").checkbox('uncheck');
                    }

                    if ($('#settings_upgrade_manual').data("upgrade-manual") === "True") {
                        $("#settings_upgrade_manual").checkbox('check');
                    } else {
                        $("#settings_upgrade_manual").checkbox('uncheck');
                    }

                    if ($('#settings_embedded').data("embedded") === "True") {
                        $("#settings_embedded").checkbox('check');
                    } else {
                        $("#settings_embedded").checkbox('uncheck');
                    }

                    if ($('#settings_ignore_pgs').data("ignorepgs") === "True") {
                        $("#settings_ignore_pgs").checkbox('check');
                    } else {
                        $("#settings_ignore_pgs").checkbox('uncheck');
                    }

                    if ($('#settings_adaptive_searching').data("adaptive") === "True") {
                        $("#settings_adaptive_searching").checkbox('check');
                    } else {
                        $("#settings_adaptive_searching").checkbox('uncheck');
                    }

                    if ($('#settings_multithreading').data("multithreading") === "True") {
                        $("#settings_multithreading").checkbox('check');
                    } else {
                        $("#settings_multithreading").checkbox('uncheck');
                    }

                    if ($('#settings_utf8_encode').data("utf8encode") === "True") {
                        $("#settings_utf8_encode").checkbox('check');
                    } else {
                        $("#settings_utf8_encode").checkbox('uncheck');
                    }

                    if (($('#settings_subfolder').val() !== "relative") && ($('#settings_subfolder').val() !== "absolute")) {
                        $('.subfolder').hide();
                    }

                    $('#settings_subfolder').dropdown('setting', 'onChange', function(){
                        if (($('#settings_subfolder').val() !== "relative") && ($('#settings_subfolder').val() !== "absolute")) {
                            $('.subfolder').hide();
                        }
                        else {
                            $('.subfolder').show();
                        }
                    });

                    if ($('#settings_anti_captcha_provider').val() === "None") {
                        $('.anticaptcha').hide();
                        $('.deathbycaptcha').hide();
                    } else if ($('#settings_anti_captcha_provider').val() === "anti-captcha") {
                        $('.anticaptcha').show();
                        $('.deathbycaptcha').hide();
                    } else if ($('#settings_anti_captcha_provider').val() === "death-by-cCaptcha") {
                        $('.deathbycaptcha').show();
                        $('.anticaptcha').hide();
                    }

                    $('#settings_anti_captcha_provider').dropdown('setting', 'onChange', function(){
                        if ($('#settings_anti_captcha_provider').val() === "None") {
                            $('.anticaptcha').hide();
                            $('.deathbycaptcha').hide();
                        } else if ($('#settings_anti_captcha_provider').val() === "anti-captcha") {
                            $('.anticaptcha').show();
                            $('.deathbycaptcha').hide();
                        } else if ($('#settings_anti_captcha_provider').val() === "death-by-captcha") {
                            $('.deathbycaptcha').show();
                            $('.anticaptcha').hide();
                        }
                    });

                    if ($('#settings_upgrade_subs').data("upgrade") === "True") {
                        $('.upgrade_subs').show();
                    } else {
                        $('.upgrade_subs').hide();
                    }

                    $('#settings_upgrade_subs').checkbox({
                        onChecked: function() {
                            $('.upgrade_subs').show();
                        },
                        onUnchecked: function() {
                            $('.upgrade_subs').hide();
                        }
                    });

                    $('#settings_languages').dropdown('setting', 'onAdd', function(val, txt){
                        $("#settings_serie_default_languages").append(
                            $("<option></option>").attr("value", val).text(txt)
                        );
                        $("#settings_movie_default_languages").append(
                            $("<option></option>").attr("value", val).text(txt)
                        )
                    });

                    $('#settings_languages').dropdown('setting', 'onRemove', function(val, txt){
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

                    $('#settings_subfolder').dropdown('clear');
                    $('#settings_subfolder').dropdown('set selected', '{{!settings.general.subfolder}}');
                    $('#settings_anti_captcha_provider').dropdown('clear');
                    $('#settings_anti_captcha_provider').dropdown('set selected', '{{!settings.general.anti_captcha_provider}}');
                    $('#settings_languages').dropdown('clear');
                    $('#settings_languages').dropdown('set selected',{{!enabled_languages}});

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


                </script>