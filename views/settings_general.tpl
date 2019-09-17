                <div class="ui dividing header">Start-Up</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Listening IP Address</label>
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
                                <div class="ui basic icon" data-tooltip="Valid IP4 Address or '0.0.0.0' for all interfaces" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Listening Port</label>
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
                                <label>Enable Debug Logging</label>
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
                                <label>Enable CHMOD</label>
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
                                <label>Set Subtitle file permissions to</label>
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
                                <label>Page Size</label>
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
                                <label>Proxy Type</label>
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

                <div class="ui dividing header">Security Settings</div>
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
                                    <div class="ui basic icon" data-tooltip="Authentication send username and password in clear text over the network. You should add SSL encryption through a reverse proxy." data-inverted="">
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
                                    <div class="ui basic icon" data-tooltip="Enable Sonarr Integration." data-inverted="">
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
                                    <div class="ui basic icon" data-tooltip="Enable Radarr Integration." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ui dividing header">Path Mappings For TV Shows</div>
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

                <div class="ui dividing header">Path Mappings For Movies</div>
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
                        <p>Be aware that the execution of post-processing command will prevent the user interface from being accessible until completion, when downloading subtitles in interactive mode (meaning you'll see a loader during post-processing).</p>
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

                <div id="div_update">
                    <div class="ui dividing header">Updates</div>
                    <div class="twelve wide column">
                        <div class="ui grid">
                            <div class="middle aligned row" id="div_branch">
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

                            <div class="middle aligned row">
                                <div class="right aligned four wide column">
                                    <label>Restart after update</label>
                                </div>
                                <div class="one wide column">
                                    <div id="settings_update_restart" class="ui toggle checkbox"
                                         data-update-restart={{settings.general.getboolean('update_restart')}}>
                                        <input name="settings_general_update_restart" type="checkbox">
                                        <label></label>
                                    </div>
                                </div>
                                <div class="collapsed column">
                                    <div class="collapsed center aligned column">
                                        <div class="ui basic icon"
                                             data-tooltip="Automatically restart after downloading and installing updates. You will still be able to restart manually"
                                             data-inverted="">
                                            <i class="help circle large icon"></i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ui dividing header">Analytics</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Enable</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_analytics_enabled" class="ui toggle checkbox" data-analytics={{settings.analytics.getboolean('enabled')}}>
                                    <input name="settings_analytics_enabled" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div class="middle align row">
                            <div class="right aligned four wide column">

                            </div>
                            <div class="one wide column">
                                <i class="help circle large icon"></i>
                            </div>
                            <div class="ten wide column">
                                Send anonymous usage information, nothing that can identify you. This includes information on which providers you use, what languages you search for, Bazarr, Python, Sonarr, Radarr and what OS version you are using. We will use this information to prioritize features and bug fixes. Please, keep this enabled as this is the only way we have to better understand how you use Bazarr.
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                    % from get_args import args

                    % if args.no_update:
                    $("#div_update").hide();
                    % elif args.release_update:
                    $("#div_branch").hide();
                    % end
                    % import sys
                    % if sys.platform.startswith('win'):
                    $("#chmod").hide();
                    $("#chmod_enabled").hide();
                    % end

                    if ($('#settings_automatic_div').data("automatic") === "True") {
                        $("#settings_automatic_div").checkbox('check');
                    } else {
                        $("#settings_automatic_div").checkbox('uncheck');
                    }

                    if ($('#settings_update_restart').data("update-restart") === "True") {
                        $("#settings_update_restart").checkbox('check');
                    } else {
                        $("#settings_update_restart").checkbox('uncheck');
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

                    if ($('#settings_analytics_enabled').data("analytics") === "True") {
                        $("#settings_analytics_enabled").checkbox('check');
                    } else {
                        $("#settings_analytics_enabled").checkbox('uncheck');
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
                        } else {
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
                        } else {
                            $('#settings_auth_password').val('{{settings.auth.password}}');
                        }
                    });

                    $('#settings_loglevel').dropdown('clear');
                    $('#settings_loglevel').dropdown('set selected','{{!settings.general.getboolean('debug')}}');
                    $('#settings_page_size').dropdown('clear');
                    $('#settings_page_size').dropdown('set selected','{{!settings.general.page_size}}');
                    $('#settings_proxy_type').dropdown('clear');
                    $('#settings_proxy_type').dropdown('set selected','{{!settings.proxy.type}}');
                    $('#settings_branch').dropdown('clear');
                    $('#settings_branch').dropdown('set selected','{{!settings.general.branch}}');

                    $('#settings_auth_username').on('keyup', function() {
                        $('#settings_auth_password').val('');
                        $('.form').form('validate form');
                        $('#loader').removeClass('active');
                    });


                </script>
