<html lang="en">
    <head>
        <!DOCTYPE html>
        <script src="{{base_url}}static/jquery/jquery-latest.min.js"></script>
        <script src="{{base_url}}static/semantic/semantic.min.js"></script>
        <script src="{{base_url}}static/jquery/tablesort.js"></script>
        <link rel="stylesheet" href="{{base_url}}static/semantic/semantic.min.css">

        <link rel="apple-touch-icon" sizes="120x120" href="{{base_url}}static/apple-touch-icon.png">
        <link rel="icon" type="image/png" sizes="32x32" href="{{base_url}}static/favicon-32x32.png">
        <link rel="icon" type="image/png" sizes="16x16" href="{{base_url}}static/favicon-16x16.png">
        <link rel="manifest" href="{{base_url}}static/manifest.json">
        <link rel="mask-icon" href="{{base_url}}static/safari-pinned-tab.svg" color="#5bbad5">
        <link rel="shortcut icon" href="{{base_url}}static/favicon.ico">

        <meta name="msapplication-config" content="{{base_url}}static/browserconfig.xml">
        <meta name="theme-color" content="#ffffff">

        <title>Settings - Bazarr</title>

        <style>
            body {
                background-color: #272727;
            }
            #fondblanc {
                background-color: #ffffff;
                border-radius: 0;
                box-shadow: 0 0 5px 5px #ffffff;
                margin-top: 32px;
                margin-bottom: 3em;
                padding: 1em;
            }
            .ui.tabular.menu > .disabled.item {
                opacity: 0.45 !important;
                pointer-events: none !important;
            }
            .browser {
                float: left;
                border: 1px solid gray;
                width: 640px;
                height: 480px;
                margin: 20px;
            }
            [data-tooltip]:after {
                z-index: 2;
            }
        </style>
    </head>
    <body>
        <div id='loader' class="ui page dimmer">
            <div class="ui indeterminate text loader">Saving settings...</div>
        </div>

        <div class="ui modal" id="browsemodal">
            <div class="browser"></div>
        </div>

        <div id="fondblanc" class="ui container">
            <form name="wizard_form" id="wizard_form" action="{{base_url}}save_wizard" method="post" class="ui form" autocomplete="off">
            <div id="form_validation_error" class="ui error message">
                <p>Some fields are in error and you can't save settings until you have corrected them. Be sure to check in every tabs.</p>
            </div>
            <div class="ui top attached mini steps">
                <div class="active step" data-tab="general" id="general_tab">
                    <i class="setting icon"></i>
                    <div class="content">
                      <div class="title">General</div>
                      <div class="description">General settings</div>
                    </div>
                </div>
                <div class="step" data-tab="subliminal" id="subliminal_tab">
                    <i class="closed captioning icon"></i>
                    <div class="content">
                      <div class="title">Subliminal</div>
                      <div class="description">Subliminal settings</div>
                    </div>
                </div>
                <div class="step" data-tab="sonarr" id="sonarr_tab">
                    <i class="play icon"></i>
                    <div class="content">
                      <div class="title">Sonarr</div>
                      <div class="description">Sonarr settings</div>
                    </div>
                </div>
                <div class="step" data-tab="radarr" id="radarr_tab">
                    <i class="film icon"></i>
                    <div class="content">
                      <div class="title">Radarr</div>
                      <div class="description">Radarr settings</div>
                    </div>
                </div>
            </div>
            <div class="ui bottom attached tab segment active" data-tab="general" id="general">
                <div class="ui container"><button class="submit ui blue right floated right labeled icon button next1">
                    <i class="right arrow icon"></i>
                    Next
                </button></div>
                <div class="ui dividing header">Start-Up</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Listening IP address</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input name="settings_general_ip" type="text" value="{{settings.general.ip}}">
                                    </div>
                                </div>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Requires restart to take effect" data-inverted="">
                                    <i class="yellow warning sign icon"></i>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Valid IP4 address or '0.0.0.0' for all interfaces" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Listening port</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input name="settings_general_port" type="text" value="{{settings.general.port}}">
                                    </div>
                                </div>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Requires restart to take effect" data-inverted="">
                                    <i class="yellow warning sign icon"></i>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Valid TCP port (default: 6767)" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Base URL</label>
                            </div>
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    %if settings.general.base_url is None:
                                    %	base_url = "/"
                                    %else:
                                    %	base_url = settings.general.base_url
                                    %end
                                    <input name="settings_general_baseurl" type="text">
                                </div>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Requires restart to take effect" data-inverted="">
                                    <i class="yellow warning sign icon"></i>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="For reverse proxy support, default is '/'" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ui dividing header">Path Mappings for shows</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        %import ast
                        %if settings.general.path_mappings is not None:
                        %	path_substitutions = ast.literal_eval(settings.general.path_mappings)
                        %else:
                        %	path_substitutions = []
                        %end
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">

                            </div>
                            <div class="two wide column">
                                <div class="ui fluid input">
                                    <h4 class="ui header">
                                        Path for Sonarr:
                                    </h4>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Root path to the directory Sonarr accesses." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                            <div class="two wide center aligned column">

                            </div>
                            <div class="two wide column">
                                <div class="ui fluid input">
                                    <h4 class="ui header">
                                        Path for Bazarr:
                                    </h4>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Path that Bazarr should use to access the same directory remotely." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        %for x in range(0, 5):
                        %	path = []
                        %	try:
                        %		path = path_substitutions[x]
                        %	except IndexError:
                        %		path = ["", ""]
                        %	end
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">

                            </div>
                            <div class="four wide column">
                                <div class="ui fluid input">
                                    <input name="settings_general_sourcepath" type="text">
                                </div>
                            </div>
                            <div class="center aligned column">
                                <i class="arrow circle right icon"></i>
                            </div>
                            <div class="four wide column">
                                <div class="ui fluid input">
                                    <input name="settings_general_destpath" type="text">
                                </div>
                            </div>
                        </div>
                        %end
                    </div>
                </div>

                <div class="ui dividing header">Path Mappings for movies</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        %import ast
                        %if settings.general.path_mappings_movie is not None:
                        %	path_substitutions_movie = ast.literal_eval(settings.general.path_mappings_movie)
                        %else:
                        %	path_substitutions_movie = []
                        %end
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">

                            </div>
                            <div class="two wide column">
                                <div class="ui fluid input">
                                    <h4 class="ui header">
                                        Path for Radarr:
                                    </h4>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Root path to the directory Radarr accesses." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                            <div class="two wide center aligned column">

                            </div>
                            <div class="two wide column">
                                <div class="ui fluid input">
                                    <h4 class="ui header">
                                        Path for Bazarr:
                                    </h4>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Path that Bazarr should use to access the same directory remotely." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        %for x in range(0, 5):
                        %	path_movie = []
                        %	try:
                        %		path_movie = path_substitutions_movie[x]
                        %	except IndexError:
                        %		path_movie = ["", ""]
                        %	end
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">

                            </div>
                            <div class="four wide column">
                                <div class="ui fluid input">
                                    <input name="settings_general_sourcepath_movie" type="text">
                                </div>
                            </div>
                            <div class="center aligned column">
                                <i class="arrow circle right icon"></i>
                            </div>
                            <div class="four wide column">
                                <div class="ui fluid input">
                                    <input name="settings_general_destpath_movie" type="text">
                                </div>
                            </div>
                        </div>
                        %end
                    </div>
                </div>
            </div>
            <div class="ui bottom attached tab segment" data-tab="subliminal" id="subliminal">

                <div class="ui container">
                    <button class="submit ui blue right floated right labeled icon button next2">
                    <i class="right arrow icon"></i>
                    Next
                </button>
                    <button class="submit ui blue right floated left labeled icon button prev1">
                    <i class="left arrow icon"></i>
                    Prev
                </button>
                    </div>
                <div class="ui dividing header">Subtitles providers</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Addic7ed</label>
                            </div>
                            <div class="one wide column">
                                <div id="addic7ed" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="addic7ed_option" class="ui grid container">
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Username</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_addic7ed_username" type="text" value="{{settings.addic7ed.username if settings.addic7ed.username != None else ''}}">
                                    </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Password</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_addic7ed_password" type="password" value="{{settings.addic7ed.password if settings.addic7ed.password != None else ''}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>LegendasTV</label>
                            </div>
                            <div class="one wide column">
                                <div id="legendastv" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="legendastv_option" class="ui grid container">
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Username</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_legendastv_username" type="text" value="{{settings.legendastv.username if settings.legendastv.username != None else ''}}">
                                    </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Password</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_legendastv_password" type="password" value="{{settings.legendastv.password if settings.legendastv.password != None else ''}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>OpenSubtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="opensubtitles" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="opensubtitles_option" class="ui grid container">
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Username</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_opensubtitles_username" type="text" value="{{settings.opensubtitles.username if settings.opensubtitles.username != None else ''}}">
                                    </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Password</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_opensubtitles_password" type="password" value="{{settings.opensubtitles.password if settings.opensubtitles.password != None else ''}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Podnapisi</label>
                            </div>
                            <div class="one wide column">
                                <div id="podnapisi" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="podnapisi_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Shooter</label>
                            </div>
                            <div class="one wide column">
                                <div id="shooter" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="shooter_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subscenter</label>
                            </div>
                            <div class="one wide column">
                                <div id="subscenter" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="subcenter_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>TheSubDB</label>
                            </div>
                            <div class="one wide column">
                                <div id="thesubdb" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="thesubdb_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>TVSubtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="tvsubtitles" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="tvsubtitles_option" class="ui grid container">

                        </div>


                        <div class="middle aligned row">
                            <div class="eleven wide column">
                                <div class='field' hidden>
                                    <select name="settings_subliminal_providers" id="settings_providers" multiple="" class="ui fluid search selection dropdown">
                                        <option value="">Providers</option>
                                        %enabled_providers = []
                                        %providers = settings.general.enabled_providers.lower().split(',')
                                        %for provider in settings_providers:
                                        <option value="{{provider}}">{{provider}}</option>
                                        %end
                                        %for provider in providers:
                                        %enabled_providers.append(str(provider))
                                        %end
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="ui dividing header">Subtitles languages</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Single language</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_single_language" class="ui toggle checkbox"  data-single-language={{settings.general.getboolean('single_language')}}>
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
                                    <div id="settings_serie_default_enabled_div" class="ui toggle checkbox">
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
                                <label>Hearing-impaired</label>
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
                                    <div id="settings_movie_default_enabled_div" class="ui toggle checkbox">
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
                                <label>Hearing-impaired</label>
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
                    </div>
                </div>
            </div>
            <div class="ui bottom attached tab segment" data-tab="sonarr" id="sonarr">

                <div class="ui container"><button class="submit ui blue right floated right labeled icon button next3">
                    <i class="right arrow icon"></i>
                    Next
                </button>
                <button class="submit ui blue right floated left labeled icon button prev2">
                    <i class="left arrow icon"></i>
                    Prev
                </button></div>

                <div class="ui dividing header">Connection settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Settings validation:</label>
                            </div>
                            <div class="two wide column">
                                <button id="sonarr_validate" class="test ui blue button" type="button">
                                    Test
                                </button>
                            </div>
                            <div class="seven wide column">
                                <div id="sonarr_validated" class="ui read-only checkbox">
                                    <input id="sonarr_validated_checkbox" type="checkbox">
                                    <label id="sonarr_validation_result">Not tested recently</label>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Use Sonarr</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_use_sonarr" class="ui toggle checkbox">
                                    <input name="settings_general_use_sonarr" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Enable Sonarr integration." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="sonarr_hide middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Hostname or IP address</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_sonarr_ip" name="settings_sonarr_ip" class="sonarr_config" type="text" value="{{settings.sonarr.ip}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Hostname or IP4 address of Sonarr" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="sonarr_hide middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Listening port</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_sonarr_port" name="settings_sonarr_port" class="sonarr_config" type="text" value="{{settings.sonarr.port}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="TCP port of Sonarr" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="sonarr_hide middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Base URL</label>
                            </div>
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <input id="settings_sonarr_baseurl" name="settings_sonarr_baseurl" class="sonarr_config" type="text">
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Base URL for Sonarr (default: '/')" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="sonarr_hide middle aligned row">
                            <div class="right aligned four wide column">
                                <label>SSL enabled</label>
                            </div>
                            <div class="one wide column">
                                <div id="sonarr_ssl_div" class="ui toggle checkbox">
                                    <input id="settings_sonarr_ssl" name="settings_sonarr_ssl" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>

                        <div class="sonarr_hide middle aligned row">
                            <div class="right aligned four wide column">
                                <label>API key</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_sonarr_apikey" name="settings_sonarr_apikey" class="sonarr_config" type="text">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="API key for Sonarr (32 alphanumeric characters)" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="sonarr_hide middle aligned row">
                        <div class="right aligned four wide column">
                            <label>Download only monitored</label>
                        </div>
                        <div class="one wide column">
                            <div id="settings_only_monitored_sonarr" class="ui toggle checkbox" data-monitored={{settings.sonarr.getboolean('only_monitored')}}>
                                <input name="settings_sonarr_only_monitored" type="checkbox">
                                <label></label>
                            </div>
                        </div>
                        <div class="collapsed column">
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Automatic download of subtitles will happen only for monitored episodes in Sonarr." data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                    </div>
                </div>

            </div>
            <div class="ui bottom attached tab segment" data-tab="radarr" id="radarr">

                <div class="ui container"><button class="submit ui blue right floated lright labeled icon button" id="submit" type="submit" value="Submit" form="wizard_form"><i class="save icon"></i>Save</button>
                <button class="submit ui blue right floated left labeled icon button prev3">
                    <i class="left arrow icon"></i>
                    Prev
                </button></div>

                <div class="ui dividing header">Connection settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Settings validation:</label>
                            </div>
                            <div class="two wide column">
                                <button id="radarr_validate" class="test ui blue button" type="button">
                                    Test
                                </button>
                            </div>
                            <div class="seven wide column">
                                <div id="radarr_validated" class="ui read-only checkbox">
                                    <input id="radarr_validated_checkbox" type="checkbox">
                                    <label id="radarr_validation_result">Not tested recently</label>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Use Radarr</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_use_radarr" class="ui toggle checkbox">
                                    <input name="settings_general_use_radarr" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Enable Radarr integration." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="radarr_hide middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Hostname or IP address</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_radarr_ip" name="settings_radarr_ip" type="text" class="radarr_config" value="{{settings.radarr.ip}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Hostname or IP4 address of Radarr" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="radarr_hide middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Listening port</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_radarr_port" name="settings_radarr_port" type="text" class="radarr_config" value="{{settings.radarr.port}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="TCP port of Radarr" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="radarr_hide middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Base URL</label>
                            </div>
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <input id="settings_radarr_baseurl" name="settings_radarr_baseurl" type="text" class="radarr_config">
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Base URL for Radarr (default: '/')" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="radarr_hide middle aligned row">
                            <div class="right aligned four wide column">
                                <label>SSL enabled</label>
                            </div>
                            <div class="one wide column">
                                <div id="radarr_ssl_div" class="ui toggle checkbox">
                                    <input id="settings_radarr_ssl" name="settings_radarr_ssl" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>

                        <div class="radarr_hide middle aligned row">
                            <div class="right aligned four wide column">
                                <label>API key</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_radarr_apikey" name="settings_radarr_apikey" type="text" class="radarr_config">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="API key for Radarr (32 alphanumeric characters)" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="radarr_hide middle aligned row">
                        <div class="right aligned four wide column">
                            <label>Download only monitored</label>
                        </div>
                        <div class="one wide column">
                            <div id="settings_only_monitored_radarr" class="ui toggle checkbox" data-monitored={{settings.radarr.getboolean('only_monitored')}}>
                                <input name="settings_radarr_only_monitored" type="checkbox">
                                <label></label>
                            </div>
                        </div>
                        <div class="collapsed column">
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Automatic download of subtitles will happen only for monitored movies in Radarr." data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                    </div>
                </div>

            </div>
            </form>
        </div>
        % include('footer.tpl')
    </body>
</html>

<script>
    function getQueryVariable(variable)
    {
           var query = window.location.search.substring(1);
           var vars = query.split("&");
           for (var i=0;i<vars.length;i++) {
                   var pair = vars[i].split("=");
                   if(pair[0] == variable){return pair[1];}
           }
           return(false);
    }

    if (getQueryVariable("saved") == 'true') {
        new Noty({
			text: 'Settings saved.',
			timeout: 5000,
			progressBar: false,
			animation: {
				open: null,
				close: null
			},
			killer: true,
    		type: 'info',
			layout: 'bottomRight',
			theme: 'semanticui'
		}).show();
    }

$(function() {

  $('.next1').on('click', function(e) {

    e.preventDefault();

    $('#general').removeClass('active');
    $('#subliminal').addClass('active');
    $('#subliminal_tab').addClass('active');
    $('#general_tab').removeClass('active');
    $('#general_tab').addClass('completed');

  });

  $('.prev1').on('click', function(m) {

    m.preventDefault();

    $('#general').addClass('active');
    $('#subliminal').removeClass('active');
    $('#subliminal_tab').removeClass('active');
    $('#general_tab').removeClass('completed');
    $('#general_tab').addClass('active');

  });

  $('.next2').on('click', function(e) {

    e.preventDefault();

    $('#subliminal').removeClass('active');
    $('#sonarr').addClass('active');
    $('#sonarr_tab').addClass('active');
    $('#subliminal_tab').removeClass('active');
    $('#subliminal_tab').addClass('completed');

  });

  $('.prev2').on('click', function(m) {

    m.preventDefault();

    $('#subliminal').addClass('active');
    $('#sonarr').removeClass('active');
    $('#sonarr_tab').removeClass('active');
    $('#subliminal_tab').removeClass('completed');
    $('#subliminal_tab').addClass('active');

  });

  $('.next3').on('click', function(e) {

    e.preventDefault();

    $('#sonarr').removeClass('active');
    $('#radarr').addClass('active');
    $('#radarr_tab').addClass('active');
    $('#sonarr_tab').removeClass('active');
    $('#sonarr_tab').addClass('completed');

  });

  $('.prev3').on('click', function(m) {

    m.preventDefault();

    $('#sonarr').addClass('active');
    $('#radarr').removeClass('active');
    $('#radarr_tab').removeClass('active');
    $('#sonarr_tab').removeClass('completed');
    $('#sonarr_tab').addClass('active');

  });

});

    $(".sonarr_hide").hide();
    $('#settings_use_sonarr').checkbox({
        onChecked: function() {
            $(".sonarr_hide").show();
        },
        onUnchecked: function() {
            $(".sonarr_hide").hide();
        }
    });

    $(".radarr_hide").hide();
    $('#settings_use_radarr').checkbox({
        onChecked: function() {
            $(".radarr_hide").show();
        },
        onUnchecked: function() {
            $(".radarr_hide").hide();
        }
    });

    if ($('#sonarr_ssl_div').data("ssl") === "True") {
                $("#sonarr_ssl_div").checkbox('check');
            } else {
                $("#sonarr_ssl_div").checkbox('uncheck');
            }

    if ($('#radarr_ssl_div').data("ssl") === "True") {
                $("#radarr_ssl_div").checkbox('check');
            } else {
                $("#radarr_ssl_div").checkbox('uncheck');
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
    } else {
        $("#settings_serie_default_languages").addClass('disabled');
        $("#settings_serie_default_hi_div").addClass('disabled');
    }

    $('#settings_serie_default_enabled_div').checkbox({
        onChecked: function() {
            $("#settings_serie_default_languages").parent().removeClass('disabled');
            $("#settings_serie_default_hi_div").removeClass('disabled');
        },
        onUnchecked: function() {
            $("#settings_serie_default_languages").parent().addClass('disabled');
            $("#settings_serie_default_hi_div").addClass('disabled');
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
    } else {
        $("#settings_movie_default_languages").addClass('disabled');
        $("#settings_movie_default_hi_div").addClass('disabled');
    }

    if ($('#settings_only_monitored_sonarr').data("monitored") === "True") {
                $("#settings_only_monitored_sonarr").checkbox('check');
            } else {
                $("#settings_only_monitored_sonarr").checkbox('uncheck');
            }

    if ($('#settings_only_monitored_radarr').data("monitored") === "True") {
                $("#settings_only_monitored_radarr").checkbox('check');
            } else {
                $("#settings_only_monitored_radarr").checkbox('uncheck');
            }

    $('#settings_movie_default_enabled_div').checkbox({
        onChecked: function() {
            $("#settings_movie_default_languages").parent().removeClass('disabled');
            $("#settings_movie_default_hi_div").removeClass('disabled');
        },
        onUnchecked: function() {
            $("#settings_movie_default_languages").parent().addClass('disabled');
            $("#settings_movie_default_hi_div").addClass('disabled');
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

    $('#settings_providers').dropdown('clear');
    $('#settings_providers').dropdown('set selected',{{!enabled_providers}});
    $('#settings_languages').dropdown('clear');
    $('#settings_languages').dropdown('set selected',{{!enabled_languages}});

    $('#settings_providers').dropdown();
    $('#settings_languages').dropdown();
    $('#settings_serie_default_languages').dropdown();
    $('#settings_movie_default_languages').dropdown();
    %if settings.general.serie_default_language is not None:
    $('#settings_serie_default_languages').dropdown('set selected',{{!settings.general.serie_default_language}});
    %end
    %if settings.general.movie_default_language is not None:
    $('#settings_movie_default_languages').dropdown('set selected',{{!settings.general.movie_default_language}});
    %end

    // form validation
    $('#wizard_form')
        .form({
            fields: {
                settings_general_ip	: {
                    rules : [
                        {
                            type : 'regExp[/^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/]'
                        },
                        {
                            type : 'empty'
                        }
                    ]
                },
                settings_general_port : {
                    rules : [
                        {
                            type : 'integer[1..65535]'
                        },
                        {
                            type : 'empty'
                        }
                    ]
                },
                sonarr_validated_checkbox : {
                    depends: 'settings_general_use_sonarr',
                    rules : [
                        {
                            type : 'checked'
                        }
                    ]
                },
                settings_sonarr_ip : {
                    depends: 'settings_general_use_sonarr',
                    rules : [
                        {
                            type : 'empty'
                        }
                    ]
                },
                settings_sonarr_port : {
                    depends: 'settings_general_use_sonarr',
                    rules : [
                        {
                            type : 'integer[1..65535]'
                        },
                        {
                            type : 'empty'
                        }
                    ]
                },
                settings_sonarr_apikey : {
                    depends: 'settings_general_use_sonarr',
                    rules : [
                        {
                            type : 'exactLength[32]'
                        },
                        {
                            type : 'empty'
                        }
                    ]
                },
                radarr_validated_checkbox : {
                    depends: 'settings_general_use_radarr',
                    rules : [
                        {
                            type : 'checked'
                        }
                    ]
                },
                settings_radarr_ip : {
                    depends: 'settings_general_use_radarr',
                    rules : [
                        {
                            type : 'empty'
                        }
                    ]
                },
                settings_radarr_port : {
                    depends: 'settings_general_use_radarr',
                    rules : [
                        {
                            type : 'integer[1..65535]'
                        },
                        {
                            type : 'empty'
                        }
                    ]
                },
                settings_radarr_apikey : {
                    depends: 'settings_general_use_radarr',
                    rules : [
                        {
                            type : 'exactLength[32]'
                        },
                        {
                            type : 'empty'
                        }
                    ]
                },
                settings_subliminal_providers : {
                    rules : [
                        {
                            type : 'minCount[1]'
                        },
                        {
                            type : 'empty'
                        }
                    ]
                },
                settings_subliminal_languages : {
                    rules : [
                        {
                            type : 'minCount[1]'
                        },
                        {
                            type : 'empty'
                        }
                    ]
                }
            },
            inline : true,
            on     : 'blur',
            onFailure: function(){
                $('#form_validation_error').show();
                $('#submit').addClass('disabled');
                $('.prev2').addClass('disabled');
                $('.prev3').addClass('disabled');
                $('.next2').addClass('disabled');
                $('.next3').addClass('disabled');


                return false;
            },
            onSuccess: function(){
                $('#form_validation_error').hide();
                $('#submit').removeClass('disabled');
                $('.prev2').removeClass('disabled');
                $('.prev3').removeClass('disabled');
                $('.next2').removeClass('disabled');
                $('.next3').removeClass('disabled');
            }
        })
    ;

    $("#settings_providers > option").each(function() {
        $('#'+$(this).val()+'_option').hide();
    });

    $("#settings_providers > option:selected").each(function() {
        $('[id='+this.value+']').checkbox('check');
        $('#'+$(this).val()+'_option').show();
    });

    $('.provider').checkbox({
        onChecked: function() {
            $('#settings_providers').dropdown('set selected', $(this).parent().attr('id'));
            $('#'+$(this).parent().attr('id')+'_option').show();
        },
        onUnchecked: function() {
            $('#settings_providers').dropdown('remove selected', $(this).parent().attr('id'));
            $('#'+$(this).parent().attr('id')+'_option').hide();
        }
    });

    $('#settings_languages').dropdown('setting', 'onChange', function(){
        $('.form').form('validate field', 'settings_subliminal_languages');
    });

    $(function() {
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });

    $('#wizard_form').on('focusout', function() {
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });


    $('#sonarr_validate').on('click', function() {
        if ($('#sonarr_ssl_div').checkbox('is checked')) {
            protocol = 'https';
        } else {
            protocol = 'http';
        }
        sonarr_url = $('#settings_sonarr_ip').val() + ":" + $('#settings_sonarr_port').val() + $('#settings_sonarr_baseurl').val().replace(/\/$/, "") + "/api/system/status?apikey=" + $('#settings_sonarr_apikey').val();

        $.getJSON("{{base_url}}test_url/" + protocol + "/" + encodeURIComponent(sonarr_url), function (data) {
            if (data.status) {
                $('#sonarr_validated').checkbox('check');
                $('#sonarr_validation_result').text('Test successful: Sonarr v' + data.version).css('color', 'green');
                $('.form').form('validate form');
                $('#loader').removeClass('active');
            } else {
                $('#sonarr_validated').checkbox('uncheck');
                $('#sonarr_validation_result').text('Test failed').css('color', 'red');
                $('.form').form('validate form');
                $('#loader').removeClass('active');
            }
        });
    });

    $('.sonarr_config').on('keyup', function() {
        $('#sonarr_validated').checkbox('uncheck');
        $('#sonarr_validation_result').text('You must test your Sonarr connection settings before saving settings.').css('color', 'red');
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });

    $('#settings_sonarr_ssl').on('change', function() {
        $('#sonarr_validated').checkbox('uncheck');
        $('#sonarr_validation_result').text('You must test your Sonarr connection settings before saving settings.').css('color', 'red');
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });

    $("#sonarr_validated").checkbox('check');

    $('#radarr_validate').on('click', function() {
        if ($('#radarr_ssl_div').checkbox('is checked')) {
            protocol = 'https';
        } else {
            protocol = 'http';
        }
        radarr_url = $('#settings_radarr_ip').val() + ":" + $('#settings_radarr_port').val() + $('#settings_radarr_baseurl').val().replace(/\/$/, "") + "/api/system/status?apikey=" + $('#settings_radarr_apikey').val();

        $.getJSON("{{base_url}}test_url/" + protocol + "/" + encodeURIComponent(radarr_url), function (data) {
            if (data.status) {
                $('#radarr_validated').checkbox('check');
                $('#radarr_validation_result').text('Test successful: Radarr v' + data.version).css('color', 'green');
                $('.form').form('validate form');
                $('#loader').removeClass('active');
            } else {
                $('#radarr_validated').checkbox('uncheck');
                $('#radarr_validation_result').text('Test failed').css('color', 'red');
                $('.form').form('validate form');
                $('#loader').removeClass('active');
            }
        });
    });

    $('.radarr_config').on('keyup', function() {
        $('#radarr_validated').checkbox('uncheck');
        $('#radarr_validation_result').text('You must test your Sonarr connection settings before saving settings.').css('color', 'red');
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });

    $('#settings_radarr_ssl').on('change', function() {
        $('#radarr_validated').checkbox('uncheck');
        $('#radarr_validation_result').text('You must test your Sonarr connection settings before saving settings.').css('color', 'red');
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });

    $("#radarr_validated").checkbox('check');
</script>
