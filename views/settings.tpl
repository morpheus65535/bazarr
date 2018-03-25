<html>
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
                border-radius: 0px;
                box-shadow: 0px 0px 5px 5px #ffffff;
                margin-top: 32px;
                margin-bottom: 3em;
                padding: 1em;
            }
        </style>
    </head>
    <body>
        <div id='loader' class="ui page dimmer">
            <div class="ui indeterminate text loader">Loading...</div>
        </div>
        % include('menu.tpl')

        <div id="fondblanc" class="ui container">
            <form name="settings_form" id="settings_form" action="{{base_url}}save_settings" method="post" class="ui form">
            <div id="form_validation_error" class="ui error message">
                <p>Some fields are in error and you can't save settings until you have corrected them.</p>
            </div>
            <div class="ui top attached tabular menu">
                <a class="tabs item active" data-tab="general">General</a>
                <a class="tabs item" data-tab="sonarr">Sonarr</a>
                <a class="tabs item" data-tab="subliminal">Subliminal</a>
                <a class="tabs item" data-tab="notifier">Notifications</a>
            </div>
            <div class="ui bottom attached tab segment active" data-tab="general">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
                <div class="ui dividing header">Bazarr settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Listening IP address</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input name="settings_general_ip" type="text" value="{{settings_general[0]}}">
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
                                        <input name="settings_general_port" type="text" value="{{settings_general[1]}}">
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
                                    %if settings_general[2] == None:
                                    %	base_url = "/"
                                    %else:
                                    %	base_url = settings_general[2]
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
                                <label>Log Level</label>
                            </div>
                            <div class="five wide column">
                                <select name="settings_general_loglevel" id="settings_loglevel" class="ui fluid selection dropdown">
                                    <option value="">Log Level</option>
                                    <option value="DEBUG">Debug</option>
                                    <option value="INFO">Info</option>
                                    <option value="WARNING">Warning</option>
                                    <option value="ERROR">Error</option>
                                    <option value="CRITICAL">Critical</option>
                                </select>
                            </div>

                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Requires restart to take effect" data-inverted="">
                                    <i class="yellow warning sign icon"></i>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Debug logging should only be enabled temporarily" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ui dividing header">Path Mappings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        %import ast
                        %if settings_general[3] is not None:
                        %	path_substitutions = ast.literal_eval(settings_general[3])
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

                <div class="ui dividing header">Post-processing</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Use post-processing</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_use_postprocessing" class="ui toggle checkbox" data-postprocessing={{settings_general[12]}}>
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

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Post-processing command</label>
                            </div>
                            <div class="five wide column">
                                <div id="settings_general_postprocessing_cmd_div" class="ui fluid input">
                                    <input name="settings_general_postprocessing_cmd" type="text" value="{{settings_general[13] if settings_general[13] != None else ''}}">
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="You can use those variables in your command (include the double curly brace): \n&lbrace;&lbrace;directory&rbrace;&rbrace; \n&lbrace;&lbrace;episode&rbrace;&rbrace; \n&lbrace;&lbrace;episode_name&rbrace;&rbrace; \n&lbrace;&lbrace;subtitles&rbrace;&rbrace; \n&lbrace;&lbrace;subtitles_language&rbrace;&rbrace; \n&lbrace;&lbrace;subtitles_language_code2&rbrace;&rbrace; \n&lbrace;&lbrace;subtitles_language_code3&rbrace;&rbrace;" data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

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
                                <div id="settings_automatic_div" class="ui toggle checkbox" data-automatic={{settings_general[6]}}>
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
            <div class="ui bottom attached tab segment" data-tab="sonarr">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
                <div class="ui dividing header">Sonarr settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Hostname or IP address</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input name="settings_sonarr_ip" type="text" value="{{settings_sonarr[0]}}">
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
                                        <input name="settings_sonarr_port" type="text" value="{{settings_sonarr[1]}}">
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
                                    <input name="settings_sonarr_baseurl" type="text" value="{{settings_sonarr[2]}}">
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
                                <div id="sonarr_ssl_div" class="ui toggle checkbox" data-ssl={{settings_sonarr[3]}}>
                                    <input name="settings_sonarr_ssl" type="checkbox">
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
                                        <input name="settings_sonarr_apikey" type="text" value="{{settings_sonarr[4]}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="API key for Sonarr (32 alphanumeric characters)" data-inverted="">
                                    <i class="help circle large icon"></i>
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
                                <label>Use Sonarr scene naming</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_scenename" class="ui toggle checkbox" data-scenename={{settings_general[11]}}>
                                    <input name="settings_general_scenename" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Use the scene name from Sonarr if available to circumvent usage of episode file renaming." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Minimum score</label>
                            </div>
                            <div class="two wide column">
                                <div class='field'>
                                    <div class="ui input">
                                        <input name="settings_general_minimum_score" type="number" min="0" max="100" step="5" onkeydown="return false" value="{{settings_general[10]}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Minimum score for a subtitle to be downloaded (0 to 100)." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="ui dividing header">Subtitles providers</div>
                <div class="twelve wide column">
                    <div class="ui orange message">
                        <p>Be aware that the more providers you enable, the longer it will take everytime you search for a subtitles.</p>
                    </div>
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Enabled providers</label>
                            </div>
                            <div class="eleven wide column">
                                <div class='field'>
                                    <select name="settings_subliminal_providers" id="settings_providers" multiple="" class="ui fluid selection dropdown">
                                        <option value="">Providers</option>
                                        %enabled_providers = []
                                        %for provider in settings_providers:
                                        <option value="{{provider[0]}}">{{provider[0]}}</option>
                                        %if provider[1] == True:
                                        %	enabled_providers.append(str(provider[0]))
                                        %end
                                        %end
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="ui dividing header">Providers authentication (optionnal)</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">

                            </div>
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <h4 class="ui header">Username</h4>
                                </div>
                            </div>
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <h4 class="ui header">Password (stored in clear text)</h4>
                                </div>
                            </div>
                        </div>
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>addic7ed</label>
                            </div>
                            %for provider in settings_providers:
                            %	if provider[0] == 'addic7ed':
                            %		addic7ed_username = provider[2]
                            %		addic7ed_password = provider[3]
                            %	end
                            %end
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <input name="settings_addic7ed_username" type="text" value="{{addic7ed_username if addic7ed_username != None else ''}}">
                                </div>
                            </div>
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <input name="settings_addic7ed_password" type="password" value="{{addic7ed_password if addic7ed_password != None else ''}}">
                                </div>
                            </div>
                        </div>
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>legendastv</label>
                            </div>
                            %for provider in settings_providers:
                            %	if provider[0] == 'legendastv':
                            %		legendastv_username = provider[2]
                            %		legendastv_password = provider[3]
                            %	end
                            %end
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <input name="settings_legendastv_username" type="text" value="{{legendastv_username if legendastv_username != None else ''}}">
                                </div>
                            </div>
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <input name="settings_legendastv_password" type="password" value="{{legendastv_password if legendastv_password != None else ''}}">
                                </div>
                            </div>
                        </div>
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>opensubtitles</label>
                            </div>
                            %for provider in settings_providers:
                            %	if provider[0] == 'opensubtitles':
                            %		opensubtitles_username = provider[2]
                            %		opensubtitles_password = provider[3]
                            %	end
                            %end
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <input name="settings_opensubtitles_username" type="text" value="{{opensubtitles_username if opensubtitles_username != None else ''}}">
                                </div>
                            </div>
                            <div class="five wide column">
                                <div class="ui fluid input">
                                    <input name="settings_opensubtitles_password" type="password" value="{{opensubtitles_password if opensubtitles_password != None else ''}}">
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
                                <div id="settings_single_language" class="ui toggle checkbox" data-single-language={{settings_general[9]}}>
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
                                    <select name="settings_subliminal_languages" id="settings_languages" multiple="" class="ui fluid selection dropdown">
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
    $('.menu .item')
        .tab()
    ;

    $('a:not(.tabs), button:not(.cancel)').click(function(){
        $('#loader').addClass('active');
    })

    $('a[target="_blank"]').click(function(){
        $('#loader').removeClass('active');
    })

    if ($('#sonarr_ssl_div').data("ssl") == "True") {
                $("#sonarr_ssl_div").checkbox('check');
            } else {
                $("#sonarr_ssl_div").checkbox('uncheck');
            }

    if ($('#settings_automatic_div').data("automatic") == "True") {
                $("#settings_automatic_div").checkbox('check');
            } else {
                $("#settings_automatic_div").checkbox('uncheck');
            }

    if ($('#settings_single_language').data("single-language") == "True") {
                $("#settings_single_language").checkbox('check');
            } else {
                $("#settings_single_language").checkbox('uncheck');
            }

    if ($('#settings_scenename').data("scenename") == "True") {
                $("#settings_scenename").checkbox('check');
            } else {
                $("#settings_scenename").checkbox('uncheck');
            }

    if ($('#settings_use_postprocessing').data("postprocessing") == "True") {
                $("#settings_use_postprocessing").checkbox('check');
                $("#settings_general_postprocessing_cmd_div").removeClass('disabled');
            } else {
                $("#settings_use_postprocessing").checkbox('uncheck');
                $("#settings_general_postprocessing_cmd_div").addClass('disabled');
            }

    $("#settings_use_postprocessing").change(function(i, obj) {
        if ($("#settings_use_postprocessing").checkbox('is checked')) {
                $("#settings_general_postprocessing_cmd_div").removeClass('disabled');
            } else {
                $("#settings_general_postprocessing_cmd_div").addClass('disabled');
            }
    });

    $('.notifier_enabled').each(function(i, obj) {
        if ($(this).data("enabled") == 1) {
                $(this).checkbox('check');
                $('[id=\"' + $(this).data("notifier-url-div") + '\"]').removeClass('disabled');
            } else {
                $(this).checkbox('uncheck');
                $('[id=\"' + $(this).data("notifier-url-div") + '\"]').addClass('disabled');
            }
    });

    $('.notifier_enabled').change(function(i, obj) {
        if ($(this).checkbox('is checked')) {
                $('[id=\"' + $(this).data("notifier-url-div") + '\"]').removeClass('disabled');
            } else {
                $('[id=\"' + $(this).data("notifier-url-div") + '\"]').addClass('disabled');
            }
    });


    $('#settings_loglevel').dropdown('clear');
    $('#settings_loglevel').dropdown('set selected','{{!settings_general[4]}}');
    $('#settings_providers').dropdown('clear');
    $('#settings_providers').dropdown('set selected',{{!enabled_providers}});
    $('#settings_languages').dropdown('clear');
    $('#settings_languages').dropdown('set selected',{{!enabled_languages}});
    $('#settings_branch').dropdown('clear');
    $('#settings_branch').dropdown('set selected','{{!settings_general[5]}}');

    $('#settings_loglevel').dropdown();
    $('#settings_providers').dropdown();
    $('#settings_languages').dropdown();
    $('#settings_branch').dropdown();
</script>

<script>
    // form validation
    $('#settings_form')
        .form({
            fields: {
                settings_general_ip     		: ['regExp[/^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/]', 'empty'],
                settings_general_port   		: ['integer[1..65535]', 'empty'],

                settings_sonarr_ip 				: ['empty'],
                settings_sonarr_port			: ['integer[1..65535]', 'empty'],
                settings_sonarr_apikey			: ['exactLength[32]', 'empty'],

                settings_subliminal_providers	: ['minCount[1]', 'empty'],
                settings_subliminal_languages	: ['minCount[1]', 'empty']
            },
            inline : true,
            on     : 'blur',
            onValid: function(){
                $('#form_validation_error').hide();
                $('.submit').removeClass('disabled');
            },
            onInvalid: function(){
                $('#form_validation_error').show();
                $('.submit').addClass('disabled');
            },
            onFailure: function(){
                return false;
            },
            onSuccess: function(){
                $('#loader').addClass('active');
            }
        })
    ;

    $('#settings_providers').dropdown('setting', 'onChange', function(){
        $('.form').form('validate field', 'settings_subliminal_providers');
    });
    $('#settings_languages').dropdown('setting', 'onChange', function(){
        $('.form').form('validate field', 'settings_subliminal_languages');
    });

    $('.submit').click(function() {
        alert('Settings saved.');
    })

    $( document ).ready(function() {
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });

    $('#settings_form').focusout(function() {
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    })
</script>