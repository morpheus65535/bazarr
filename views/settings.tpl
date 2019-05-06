<!DOCTYPE html>
<html lang="en">
    <head>
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
            [data-tooltip]:after {
                z-index: 2;
            }
        </style>
    </head>
    <body>
        <div id='loader' class="ui page dimmer">
            <div id="loader_text" class="ui indeterminate text loader">Saving settings...</div>
        </div>
        % include('menu.tpl')

        <div id="fondblanc" class="ui container">
            <form name="settings_form" id="settings_form" action="{{base_url}}save_settings" method="post" class="ui form" autocomplete="off">
            <div id="form_validation_error" class="ui error message">
                <p>Some fields are in error and you can't save settings until you have corrected them. Be sure to check in every tabs.</p>
            </div>
            <div class="ui top attached tabular menu">
                <a class="tabs item active" data-tab="general">General</a>
                <a class="tabs item" id="sonarr_tab" data-tab="sonarr">Sonarr</a>
                <a class="tabs item" id="radarr_tab" data-tab="radarr">Radarr</a>
                <a class="tabs item" data-tab="subliminal">Subliminal</a>
                <a class="tabs item" data-tab="notifier">Notifications</a>
            </div>
            <div class="ui bottom attached tab segment active" data-tab="general">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
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
                                    <input name="settings_general_baseurl" type="text" value="{{base_url}}">
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

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Enable debug logging</label>
                            </div>
                            <div class="five wide column">
                                <div id="settings_debug" class="ui toggle checkbox" data-debug={{settings.general.getboolean('debug')}}>
                                    <input name="settings_general_debug" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Debug logging should only be enabled temporarily" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>
                        <div id="chmod_enabled" class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Enable chmod</label>
                            </div>
                            <div class="five wide column">
                                <div id="settings_chmod_enabled" class="ui toggle checkbox" data-chmod={{settings.general.getboolean('chmod_enabled')}}>
                                    <input name="settings_general_chmod_enabled" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="chmod" class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Set subtitle file permissions to</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div id="settings_chmod" class="ui fluid input">
                                        <input name="settings_general_chmod" type="text"
                                               value={{ settings.general.chmod }}>
                                        <label></label>
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Must be 4 digit octal, e.g.: 0775" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Page size</label>
                            </div>
                            <div class="five wide column">
                                <select name="settings_page_size" id="settings_page_size" class="ui fluid selection dropdown">
                                    <option value="">Page Size</option>
                                    <option value="-1">Unlimited</option>
                                    <option value="25">25</option>
                                    <option value="50">50</option>
                                    <option value="100">100</option>
                                    <option value="250">250</option>
                                    <option value="500">500</option>
                                    <option value="1000">1000</option>
                                </select>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="How many items to show in a list." data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ui dividing header">Proxy settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Proxy type</label>
                            </div>
                            <div class="five wide column">
                                <select name="settings_proxy_type" id="settings_proxy_type" class="ui fluid selection dropdown">
                                    <option value="None">None</option>
                                    <option value="http">HTTP(S)</option>
                                    <option value="socks4">Socks4</option>
                                    <option value="socks5">Socks5</option>
                                </select>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Requires restart to take effect" data-inverted="">
                                    <i class="yellow warning sign icon"></i>
                                </div>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Type of your proxy." data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="proxy_option middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Hostname</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_proxy_url" name="settings_proxy_url" type="text" value="{{settings.proxy.url}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="proxy_option middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Port</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_proxy_port" name="settings_proxy_port" type="text" value="{{settings.proxy.port}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="proxy_option middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Username</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_proxy_username" name="settings_proxy_username" type="text" value="{{settings.proxy.username}}">
                                    </div>
                                </div>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="UYou only need to enter a username and password if one is required. Leave them blank otherwise" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="proxy_option middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Password</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_proxy_password" name="settings_proxy_password" type="password" value="{{settings.proxy.password}}">
                                    </div>
                                </div>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="You only need to enter a username and password if one is required. Leave them blank otherwise" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>

                        </div>

                        <div class="proxy_option middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Ignored Addresses</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_proxy_exclude" name="settings_proxy_exclude" type="text" value="{{settings.proxy.exclude}}">
                                    </div>
                                </div>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Use ',' as a separator, and '*.' as a wildcard for subdomains" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>

                        </div>
                    </div>
                </div>

                <div class="ui dividing header">Security settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Authentication</label>
                            </div>
                            <div class="five wide column">
                                <select name="settings_auth_type" id="settings_auth_type" class="ui fluid selection dropdown">
                                    <option value="None">None</option>
                                    <option value="basic">Basic (Browser Popup)</option>
                                    <option value="form">Forms (Login Page)</option>
                                </select>
                                    <label></label>
                                </div>


                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Requires restart to take effect" data-inverted="">
                                    <i class="yellow warning sign icon"></i>
                                </div>
                            </div>

                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Require Username and Password to access Bazarr." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="auth_option middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Username</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_auth_username" name="settings_auth_username" type="text" autocomplete="nope" value="{{settings.auth.username}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="auth_option middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Password</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_auth_password" name="settings_auth_password" type="password" autocomplete="new-password" value="{{settings.auth.password}}">
                                    </div>
                                </div>
                            </div>

                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Authentication send username and password in clear over the network. You should add SSL encryption trough a reverse proxy." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ui dividing header">Integration settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Use Sonarr</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_use_sonarr" class="ui toggle checkbox" data-enabled={{settings.general.getboolean('use_sonarr')}}>
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

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Use Radarr</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_use_radarr" class="ui toggle checkbox" data-enabled={{settings.general.getboolean('use_radarr')}}>
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
                                    <input name="settings_general_sourcepath" type="text" value="{{path[0]}}">
                                </div>
                            </div>
                            <div class="center aligned column">
                                <i class="arrow circle right icon"></i>
                            </div>
                            <div class="four wide column">
                                <div class="ui fluid input">
                                    <input name="settings_general_destpath" type="text" value="{{path[1]}}">
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
                                    <input name="settings_general_sourcepath_movie" type="text" value="{{path_movie[0]}}">
                                </div>
                            </div>
                            <div class="center aligned column">
                                <i class="arrow circle right icon"></i>
                            </div>
                            <div class="four wide column">
                                <div class="ui fluid input">
                                    <input name="settings_general_destpath_movie" type="text" value="{{path_movie[1]}}">
                                </div>
                            </div>
                        </div>
                        %end
                    </div>
                </div>

                <div class="ui dividing header">Post-processing</div>
                <div class="twelve wide column">
                    <div class="ui orange message">
                        <p>Be aware that the execution of post-processing command will prevent the user interface from being accessible until completion when downloading subtitles in interactive mode (meaning you'll see a loader during post-processing).</p>
                    </div>
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Use post-processing</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_use_postprocessing" class="ui toggle checkbox" data-postprocessing={{settings.general.getboolean('use_postprocessing')}}>
                                    <input name="settings_general_use_postprocessing" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Enable the post-processing execution after downloading a subtitles." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row postprocessing">
                            <div class="right aligned four wide column">
                                <label>Post-processing command</label>
                            </div>
                            <div class="five wide column">
                                <div id="settings_general_postprocessing_cmd_div" class="ui fluid input">
                                    <input name="settings_general_postprocessing_cmd" type="text" value="{{settings.general.postprocessing_cmd if settings.general.postprocessing_cmd != None else ''}}">
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row postprocessing">
                            <div class="right aligned four wide column">
                                <label>Variables you can use in your command (include the double curly brace):</label>
                            </div>
                            <div class="ten wide column">
                                <div class="ui list">
                                    <div class="item">
                                        <div class="header">&lbrace;&lbrace;directory&rbrace;&rbrace;</div>
                                        The full path of the episode file parent directory.
                                    </div>
                                    <div class="item">
                                        <div class="header">&lbrace;&lbrace;episode&rbrace;&rbrace;</div>
                                        The full path of the episode file.
                                    </div>
                                    <div class="item">
                                        <div class="header">&lbrace;&lbrace;episode_name&rbrace;&rbrace;</div>
                                        The filename of the episode without parent directory or extension.
                                    </div>
                                    <div class="item">
                                        <div class="header">&lbrace;&lbrace;subtitles&rbrace;&rbrace;</div>
                                        The full path of the subtitles file.
                                    </div>
                                    <div class="item">
                                        <div class="header">&lbrace;&lbrace;subtitles_language&rbrace;&rbrace;</div>
                                        The language of the subtitles file.
                                    </div>
                                    <div class="item">
                                        <div class="header">&lbrace;&lbrace;subtitles_language_code2&rbrace;&rbrace;</div>
                                        The 2-letter ISO-639 language code of the subtitles language.
                                    </div>
                                    <div class="item">
                                        <div class="header">&lbrace;&lbrace;subtitles_language_code3&rbrace;&rbrace;</div>
                                        The 3-letter ISO-639 language code of the subtitles language.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="div_update" >
                <div class="ui dividing header">Updates</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Branch</label>
                            </div>
                            <div class="five wide column">
                                <select name="settings_general_branch" id="settings_branch" class="ui fluid selection dropdown">
                                    <option value="">Branch</option>
                                    <option value="master">master</option>
                                    <option value="development">development</option>
                                </select>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Only select development branch if you want to live on the edge." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Automatic</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_automatic_div" class="ui toggle checkbox" data-automatic={{settings.general.getboolean('auto_update')}}>
                                    <input name="settings_general_automatic" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Automatically download and install updates. You will still be able to install from System: Tasks" data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                </div>
            </div>
            <div class="ui bottom attached tab segment" data-tab="sonarr">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
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

                        <div class="middle aligned row">
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

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Base URL</label>
                            </div>
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <input id="settings_sonarr_baseurl" name="settings_sonarr_baseurl" class="sonarr_config" type="text" value="{{settings.sonarr.base_url}}">
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Base URL for Sonarr (default: '/')" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>SSL enabled</label>
                            </div>
                            <div class="one wide column">
                                <div id="sonarr_ssl_div" class="ui toggle checkbox" data-ssl={{settings.sonarr.getboolean('ssl')}}>
                                    <input id="settings_sonarr_ssl" name="settings_sonarr_ssl" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>API key</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_sonarr_apikey" name="settings_sonarr_apikey" class="sonarr_config" type="text" value="{{settings.sonarr.apikey}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="API key for Sonarr (32 alphanumeric characters)" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                            <div class="middle aligned row">
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

                <div class="ui dividing header">Synchronization</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Full sync frequency</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <select name="settings_sonarr_sync" id="settings_sonarr_sync" class="ui fluid selection dropdown">
                                        <option value="Manually">Manually</option>
                                        <option value="Daily">Daily (at 4am)</option>
                                        <option value="Weekly">Weekly (sunday at 4am)</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="ui bottom attached tab segment" data-tab="radarr">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
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

                        <div class="middle aligned row">
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

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Base URL</label>
                            </div>
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <input id="settings_radarr_baseurl" name="settings_radarr_baseurl" type="text" class="radarr_config" value="{{settings.radarr.base_url}}">
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Base URL for Radarr (default: '/')" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>SSL enabled</label>
                            </div>
                            <div class="one wide column">
                                <div id="radarr_ssl_div" class="ui toggle checkbox" data-ssl={{settings.radarr.getboolean('ssl')}}>
                                    <input id="settings_radarr_ssl" name="settings_radarr_ssl" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>API key</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_radarr_apikey" name="settings_radarr_apikey" type="text" class="radarr_config" value="{{settings.radarr.apikey}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="API key for Radarr (32 alphanumeric characters)" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
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

                <div class="ui dividing header">Synchronization</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Full sync frequency</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <select name="settings_radarr_sync" id="settings_radarr_sync" class="ui fluid selection dropdown">
                                        <option value="Manually">Manually</option>
                                        <option value="Daily">Daily (at 5am)</option>
                                        <option value="Weekly">Weekly (sunday at 5am)</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="ui bottom attached tab segment" data-tab="subliminal">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
                <br><br><br>
                <div class="ui container">
                    <div class="ui info message">
                        <p>Thanks to Diaoul for his work on <a href="https://github.com/Diaoul/subliminal" target="_blank">Subliminal</a> on which Bazarr is based.</p>
                    </div>
                </div>
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
                                <div id="settings_ignore_pgs" class="ui toggle checkbox" data-ignore={{settings.general.getboolean('ignore_pgs_subs')}}>
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

                <div class="ui dividing header">Subtitles providers</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Addic7ed (require anti-captcha)</label>
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
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Random user-agents</label>
                                </div>
                                <div class="one wide column">
                                    <div id="settings_addic7ed_random_agents" class="ui toggle checkbox" data-randomagents={{settings.addic7ed.getboolean('random_agents')}}>
                                        <input type="checkbox" name="settings_addic7ed_random_agents">
                                        <label></label>
                                    </div>
                                </div>
                                <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Use random user agents" data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Argenteam</label>
                            </div>
                            <div class="one wide column">
                                <div id="argenteam" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Spanish subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="argenteam_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Assrt</label>
                            </div>
                            <div class="one wide column">
                                <div id="assrt" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Chinese subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="assrt_option" class="ui grid container">
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Token</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_assrt_token" type="text" value="{{settings.assrt.token if settings.assrt.token != None else ''}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>GreekSubtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="greeksubtitles" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Greek subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="greeksubtitles_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Hosszupuska</label>
                            </div>
                            <div class="one wide column">
                                <div id="hosszupuska" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Hungarian subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="hosszupuska_option" class="ui grid container">

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
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Brazilian Portuguese subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
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
                                <label>Napiprojekt</label>
                            </div>
                            <div class="one wide column">
                                <div id="napiprojekt" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Polish subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="napiprojekt_option" class="ui grid container">

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
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>VIP</label>
                                </div>
                                <div class="one wide column">
                                    <div id="settings_opensubtitles_vip" class="ui toggle checkbox" data-osvip={{settings.opensubtitles.getboolean('vip')}}>
                                        <input type="checkbox" name="settings_opensubtitles_vip">
                                        <label></label>
                                    </div>
                                </div>
                                <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="ad-free subs, 1000 subs/day, no-cache VIP server: http://v.ht/osvip" data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Use SSL</label>
                                </div>
                                <div class="one wide column">
                                    <div id="settings_opensubtitles_ssl" class="ui toggle checkbox" data-osssl={{settings.opensubtitles.getboolean('ssl')}}>
                                        <input type="checkbox" name="settings_opensubtitles_ssl">
                                        <label></label>
                                    </div>
                                </div>
                                <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Use SSL to connect to OpenSubtitles" data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Skip wrong FPS</label>
                                </div>
                                <div class="one wide column">
                                    <div id="settings_opensubtitles_skip_wrong_fps" class="ui toggle checkbox" data-osfps={{settings.opensubtitles.getboolean('skip_wrong_fps')}}>
                                        <input type="checkbox" name="settings_opensubtitles_skip_wrong_fps">
                                        <label></label>
                                    </div>
                                </div>
                                <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Skip subtitles with a mismatched FPS value; might lead to more results when disabled but also to more false-positives." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
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
                                <label>Subs.sab.bz</label>
                            </div>
                            <div class="one wide column">
                                <div id="subssabbz" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Bulgarian mostly subtitle provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subssabbz_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subscene</label>
                            </div>
                            <div class="one wide column">
                                <div id="subscene" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="subscene_option" class="ui grid container">

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
                        <div id="subscenter_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subsunacs.net</label>
                            </div>
                            <div class="one wide column">
                                <div id="subsunacs" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Bulgarian mostly subtitle provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subsunacs_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subs4Free</label>
                            </div>
                            <div class="one wide column">
                                <div id="subs4free" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Greek subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subs4free_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subs4Series</label>
                            </div>
                            <div class="one wide column">
                                <div id="subs4series" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Greek subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subs4series_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>SubZ</label>
                            </div>
                            <div class="one wide column">
                                <div id="subz" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Greek subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subz_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Supersubtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="supersubtitles" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="supersubtitles_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Titlovi (require anti-captcha)</label>
                            </div>
                            <div class="one wide column">
                                <div id="titlovi" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="titlovi_option" class="ui grid container">

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
                            <div class="right aligned four wide column">
                                <label>XSubs</label>
                            </div>
                            <div class="one wide column">
                                <div id="xsubs" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Greek subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="xsubs_option" class="ui grid container">
                        	<div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Username</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_xsubs_username" type="text" value="{{settings.xsubs.username if settings.xsubs.username != None else ''}}">
                                    </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Password</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_xsubs_password" type="password" value="{{settings.xsubs.password if settings.xsubs.password != None else ''}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Zimuku</label>
                            </div>
                            <div class="one wide column">
                                <div id="zimuku" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Chinese subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="zimuku_option" class="ui grid container">

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
                    </div>
                </div>
            </div>
            <div class="ui bottom attached tab segment" data-tab="notifier">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
                <div class="ui dividing header">Notifications settings</div>
                <div class="twelve wide column">
                    <div class="ui info message">
                        <p>Thanks to caronc for his work on <a href="https://github.com/caronc/apprise" target="_blank">apprise</a> on which is based the notifications system.</p>
                    </div>
                    <div class="ui info message">
                        <p>Please follow instructions on his <a href="https://github.com/caronc/apprise/wiki" target="_blank">wiki</a> to configure your notifications providers.</p>
                    </div>
                    <div class="ui grid">
                        %for notifier in settings_notifier:
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>{{notifier[0]}}</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_notifier_{{notifier[0]}}_enabled" class="notifier_enabled ui toggle checkbox" data-notifier-url-div="settings_notifier_{{notifier[0]}}_url_div" data-enabled={{notifier[2]}}>
                                    <input name="settings_notifier_{{notifier[0]}}_enabled" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="eight wide column">
                                <div class='field'>
                                    <div id="settings_notifier_{{notifier[0]}}_url_div" class="ui fluid input">
                                        <input name="settings_notifier_{{notifier[0]}}_url" type="text" value="{{notifier[1] if notifier[1] != None else ''}}">
                                        <div class="test_notification ui blue button" data-notification="{{notifier[1]}}">Test Notification</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        %end
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

    $('.test_notification').on('click', function() {
        const url_field = $(this).prev().val();
        const url_protocol = url_field.split(':')[0];
        const url_string = url_field.split('://')[1];

        $.ajax({
            url: "{{base_url}}test_notification/" + url_protocol + "/" + encodeURIComponent(url_string),
            beforeSend: function () {
                $('#loader').addClass('active');
            },
            complete: function () {
                $('#loader').removeClass('active');
            },
            cache: false
        });
    });

    % from get_args import args
    % if args.no_update:
    $("#div_update").hide();
    % end
    % import sys
    % if sys.platform.startswith('win'):
    $("#chmod").hide();
    $("#chmod_enabled").hide();
    % end

    $('.menu .item')
        .tab()
    ;

    $('a:not(.tabs), button:not(.cancel, .test)').on('click', function(){
        $('#loader').addClass('active');
    });

    $('a[target="_blank"]').on('click', function(){
        $('#loader').removeClass('active');
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

    if ($('#settings_automatic_div').data("automatic") === "True") {
                $("#settings_automatic_div").checkbox('check');
            } else {
                $("#settings_automatic_div").checkbox('uncheck');
            }

    if ($('#settings_debug').data("debug") === "True") {
                $("#settings_debug").checkbox('check');
            } else {
                $("#settings_debug").checkbox('uncheck');
            }

    if ($('#settings_chmod_enabled').data("chmod") === "True") {
                $("#settings_chmod_enabled").checkbox('check');
            } else {
                $("#settings_chmod_enabled").checkbox('uncheck');
            }

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

    if ($('#settings_ignore_pgs').data("ignore") === "True") {
                $("#settings_ignore_pgs").checkbox('check');
            } else {
                $("#settings_ignore_pgs").checkbox('uncheck');
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

    if ($('#settings_addic7ed_random_agents').data("randomagents") === "True") {
                $("#settings_addic7ed_random_agents").checkbox('check');
            } else {
                $("#settings_addic7ed_random_agents").checkbox('uncheck');
            }

    if ($('#settings_opensubtitles_vip').data("osvip") === "True") {
                $("#settings_opensubtitles_vip").checkbox('check');
            } else {
                $("#settings_opensubtitles_vip").checkbox('uncheck');
            }

    if ($('#settings_opensubtitles_ssl').data("osssl") === "True") {
                $("#settings_opensubtitles_ssl").checkbox('check');
            } else {
                $("#settings_opensubtitles_ssl").checkbox('uncheck');
            }

    if ($('#settings_opensubtitles_skip_wrong_fps').data("osfps") === "True") {
                $("#settings_opensubtitles_skip_wrong_fps").checkbox('check');
            } else {
                $("#settings_opensubtitles_skip_wrong_fps").checkbox('uncheck');
            }

    if ($('#settings_use_postprocessing').data("postprocessing") === "True") {
                $("#settings_use_postprocessing").checkbox('check');
                $("#settings_general_postprocessing_cmd_div").removeClass('disabled');
            } else {
                $("#settings_use_postprocessing").checkbox('uncheck');
                $("#settings_general_postprocessing_cmd_div").addClass('disabled');
            }

    $("#settings_use_postprocessing").on('change', function(i, obj) {
        if ($("#settings_use_postprocessing").checkbox('is checked')) {
                $("#settings_general_postprocessing_cmd_div").removeClass('disabled');
            } else {
                $("#settings_general_postprocessing_cmd_div").addClass('disabled');
            }
    });

    if ($('#settings_use_sonarr').data("enabled") === "True") {
                $("#settings_use_sonarr").checkbox('check');
                $("#sonarr_tab").removeClass('disabled');
            } else {
                $("#settings_use_sonarr").checkbox('uncheck');
                $("#sonarr_tab").addClass('disabled');
            }

    $('#settings_use_sonarr').checkbox({
        onChecked: function() {
            $("#sonarr_tab").removeClass('disabled');
            $('#sonarr_validated').checkbox('uncheck');
            $('.form').form('validate form');
            $('#loader').removeClass('active');
        },
        onUnchecked: function() {
            $("#sonarr_tab").addClass('disabled');
        }
    });

    if ($('#settings_use_radarr').data("enabled") === "True") {
                $("#settings_use_radarr").checkbox('check');
                $("#radarr_tab").removeClass('disabled');
            } else {
                $("#settings_use_radarr").checkbox('uncheck');
                $("#radarr_tab").addClass('disabled');
            }

    $('#settings_use_radarr').checkbox({
        onChecked: function() {
            $("#radarr_tab").removeClass('disabled');
            $('#radarr_validated').checkbox('uncheck');
            $('.form').form('validate form');
            $('#loader').removeClass('active');
        },
        onUnchecked: function() {
            $("#radarr_tab").addClass('disabled');
        }
    });

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

    if ($('#settings_use_postprocessing').data("postprocessing") === "True") {
                $('.postprocessing').show();
            } else {
                $('.postprocessing').hide();
            }

    $('#settings_use_postprocessing').checkbox({
        onChecked: function() {
            $('.postprocessing').show();
        },
        onUnchecked: function() {
            $('.postprocessing').hide();
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

    if ($('#settings_chmod_enabled').data("chmod") === "True") {
                $('#chmod').show();
            } else {
                $('#chmod').hide();
            }

    $('#settings_chmod_enabled').checkbox({
        onChecked: function() {
            $('#chmod').show();
        },
        onUnchecked: function() {
            $('#chmod').hide();
        }
    });

    if ($('#settings_auth_type').val() === "None") {
        $('.auth_option').hide();
    }

    $('#settings_auth_type').dropdown('setting', 'onChange', function(){
        if ($('#settings_auth_type').val() === "None") {
            $('.auth_option').hide();
        }
        else {
            $('.auth_option').show();
        }
    });

    // Load default value for Settings_auth_type
    $('#settings_auth_type').dropdown('clear');
    $('#settings_auth_type').dropdown('set selected','{{!settings.auth.type}}');

    // Remove value from Password input when changing to Form login to prevent bad password saving
    $("#settings_auth_type").on('change', function() {
        if ($(this).val() === 'form'){
            $('#settings_auth_password').val('');
            }
        else {
            $('#settings_auth_password').val('{{settings.auth.password}}');
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

    $('.notifier_enabled').each(function() {
        if ($(this).data("enabled") === 1) {
                $(this).checkbox('check');
                $('[id=\"' + $(this).data("notifier-url-div") + '\"]').removeClass('disabled');
            } else {
                $(this).checkbox('uncheck');
                $('[id=\"' + $(this).data("notifier-url-div") + '\"]').addClass('disabled');
            }
    });

    $('.notifier_enabled').on('change', function() {
        if ($(this).checkbox('is checked')) {
                $('[id=\"' + $(this).data("notifier-url-div") + '\"]').removeClass('disabled');
            } else {
                $('[id=\"' + $(this).data("notifier-url-div") + '\"]').addClass('disabled');
            }
    });


    $('#settings_loglevel').dropdown('clear');
    $('#settings_loglevel').dropdown('set selected','{{!settings.general.getboolean('debug')}}');
    $('#settings_page_size').dropdown('clear');
    $('#settings_page_size').dropdown('set selected','{{!settings.general.page_size}}');
    $('#settings_subfolder').dropdown('clear');
    $('#settings_subfolder').dropdown('set selected', '{{!settings.general.subfolder}}');
    $('#settings_anti_captcha_provider').dropdown('clear');
    $('#settings_anti_captcha_provider').dropdown('set selected', '{{!settings.general.anti_captcha_provider}}');
    $('#settings_proxy_type').dropdown('clear');
    $('#settings_proxy_type').dropdown('set selected','{{!settings.proxy.type}}');
    $('#settings_providers').dropdown('clear');
    $('#settings_providers').dropdown('set selected',{{!enabled_providers}});
    $('#settings_languages').dropdown('clear');
    $('#settings_languages').dropdown('set selected',{{!enabled_languages}});
    $('#settings_branch').dropdown('clear');
    $('#settings_branch').dropdown('set selected','{{!settings.general.branch}}');
    $('#settings_sonarr_sync').dropdown('clear');
    $('#settings_sonarr_sync').dropdown('set selected','{{!settings.sonarr.full_update}}');
    $('#settings_radarr_sync').dropdown('clear');
    $('#settings_radarr_sync').dropdown('set selected','{{!settings.radarr.full_update}}');

    $('#settings_loglevel').dropdown();
    $('#settings_providers').dropdown();
    $('#settings_languages').dropdown();
    $('#settings_serie_default_languages').dropdown();
    $('#settings_movie_default_languages').dropdown();
    %if settings.general.serie_default_language != 'None':
    $('#settings_serie_default_languages').dropdown('set selected',{{!settings.general.serie_default_language}});
    %end
    %if settings.general.movie_default_language != 'None':
    $('#settings_movie_default_languages').dropdown('set selected',{{!settings.general.movie_default_language}});
    %end
    $('#settings_branch').dropdown();
    $('#settings_sonarr_sync').dropdown();
    $('#settings_radarr_sync').dropdown();
</script>

<script>
    // form validation
    $('#settings_form')
        .form({
            on: 'blur',
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
                % if not sys.platform.startswith('win') and settings.general.getboolean('chmod_enabled'):
                settings_general_chmod: {
                    rules: [
                        {
                            type: 'regExp[^([0-7]{4})$]',
                            prompt: 'Please use only 4-digit octal (e.g.: 0775)'
                        }
                    ]
                },
                % end
                settings_auth_password : {
                    depends: 'settings_auth_username',
                    rules : [
                        {
                            type : 'empty',
                            prompt : 'This field must have a value and you must type it again if you change your username.'
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
                },
                settings_days_to_upgrade_subs : {
                    depends: 'settings_upgrade_subs',
                    rules : [
                        {
                            type : 'integer[1..30]'
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
                $('.submit').addClass('disabled');
                return false;
            },
            onSuccess: function(){
                $('#form_validation_error').hide();
                $('.submit').removeClass('disabled');
                $('#loader').addClass('active');
            }
        })
    ;

    if ($('#settings_proxy_type').val() === "None") {
        $('.proxy_option').hide();
        $('#settings_form').form('remove rule', 'settings_proxy_url', 'empty');
        $('#settings_form').form('remove rule', 'settings_proxy_port', 'empty');
        $('#settings_form').form('remove rule', 'settings_proxy_port', 'integer[1..65535]');
    }
    else {
        $('#settings_form').form('add rule', 'settings_proxy_url', 'empty');
        $('#settings_form').form('add rule', 'settings_proxy_port', 'empty');
        $('#settings_form').form('add rule', 'settings_proxy_port', 'integer[1..65535]');
    }

    $('#settings_proxy_type').dropdown('setting', 'onChange', function(){
        if ($('#settings_proxy_type').val() === "None") {
            $('.proxy_option').hide();
            $('#settings_form').form('remove rule', 'settings_proxy_url', 'empty');
            $('#settings_form').form('remove rule', 'settings_proxy_port', 'empty');
            $('#settings_form').form('remove rule', 'settings_proxy_port', 'integer[1..65535]');
        }
        else {
            $('.proxy_option').show();
            $('#settings_form').form('add rule', 'settings_proxy_url', 'empty');
            $('#settings_form').form('add rule', 'settings_proxy_port', 'empty');
            $('#settings_form').form('add rule', 'settings_proxy_port', 'integer[1..65535]');
        }
    });

    $('#settings_providers').dropdown('setting', 'onChange', function(){
        $('.form').form('validate field', 'settings_subliminal_providers');
    });

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

    $('#settings_form').on('focusout', function() {
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });

    $('#settings_auth_username').on('keyup', function() {
    	$('#settings_auth_password').val('');
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });

    $('#sonarr_validate').on('click', function() {
        if ($('#sonarr_ssl_div').checkbox('is checked')) {
            protocol = 'https';
        } else {
            protocol = 'http';
        }
        const sonarr_url = $('#settings_sonarr_ip').val() + ":" + $('#settings_sonarr_port').val() + $('#settings_sonarr_baseurl').val().replace(/\/$/, "") + "/api/system/status?apikey=" + $('#settings_sonarr_apikey').val();

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
        const radarr_url = $('#settings_radarr_ip').val() + ":" + $('#settings_radarr_port').val() + $('#settings_radarr_baseurl').val().replace(/\/$/, "") + "/api/system/status?apikey=" + $('#settings_radarr_apikey').val();

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
        $('#radarr_validation_result').text('You must test your Radarr connection settings before saving settings.').css('color', 'red');
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });

    $('#settings_radarr_ssl').on('change', function() {
        $('#radarr_validated').checkbox('uncheck');
        $('#radarr_validation_result').text('You must test your Radarr connection settings before saving settings.').css('color', 'red');
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });

    $("#radarr_validated").checkbox('check');
</script>
