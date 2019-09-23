                <div class="ui dividing header">Connection settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Settings Validation:</label>
                            </div>
                            <div class="two wide column">
                                <button id="sonarr_validate" class="test ui blue button" type="button">
                                    Test
                                </button>
                            </div>
                            <div class="seven wide column">
                                <div id="sonarr_validated" class="ui read-only checkbox">
                                    <input id="sonarr_validated_checkbox" type="checkbox">
                                    <label id="sonarr_validation_result">Not Tested Recently</label>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Hostname or IP Address</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_sonarr_ip" name="settings_sonarr_ip" class="sonarr_config" type="text" value="{{settings.sonarr.ip}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="Hostname or IP4 Address of Sonarr" data-inverted="">
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
                                        <input id="settings_sonarr_port" name="settings_sonarr_port" class="sonarr_config" type="text" value="{{settings.sonarr.port}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="TCP Port of Sonarr" data-inverted="">
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
                                <label>SSL Enabled</label>
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
                                <label>API Key</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_sonarr_apikey" name="settings_sonarr_apikey" class="sonarr_config" type="text" value="{{settings.sonarr.apikey}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="API Key for Sonarr (32 alphanumeric characters)" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Download Only Monitored</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_only_monitored_sonarr" class="ui toggle checkbox" data-monitored={{settings.sonarr.getboolean('only_monitored')}}>
                                    <input name="settings_sonarr_only_monitored" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Automatic download of Subtitles will only happen for monitored episodes in Sonarr." data-inverted="">
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
                                <label>Full Filesystem Scan</label>
                            </div>
                            <div class="three wide column">
                                <div class='field'>
                                    <select name="settings_sonarr_sync" id="settings_sonarr_sync" class="ui fluid selection dropdown">
                                        <option value="Manually">Manually</option>
                                        <option value="Daily">Daily</option>
                                        <option value="Weekly">Weekly</option>
                                    </select>
                                </div>
                            </div>
                            <div id="settings_sonarr_sync_day_div" class="three wide column">
                                <div class='field'>
                                    <select name="settings_sonarr_sync_day" id="settings_sonarr_sync_day" class="ui fluid selection dropdown">
                                        % import calendar
                                        % for idx, i in enumerate(calendar.day_name):
                                        <option value="{{idx}}">{{i}}</option>
                                        %end
                                    </select>
                                </div>
                            </div>
                            <div id="settings_sonarr_sync_hour_div" class="two wide column">
                                <div class='field'>
                                    <select name="settings_sonarr_sync_hour" id="settings_sonarr_sync_hour" class="ui fluid selection dropdown">
                                        % for i in range(24):
                                        <option value="{{i}}">{{i}}:00</option>
                                        %end
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                    if ($('#sonarr_ssl_div').data("ssl") === "True") {
                        $("#sonarr_ssl_div").checkbox('check');
                    } else {
                        $("#sonarr_ssl_div").checkbox('uncheck');
                    }

                    if ($('#settings_only_monitored_sonarr').data("monitored") === "True") {
                        $("#settings_only_monitored_sonarr").checkbox('check');
                    } else {
                        $("#settings_only_monitored_sonarr").checkbox('uncheck');
                    }

                    $('#settings_sonarr_sync').dropdown('setting', 'onChange', function(){
                        if ($('#settings_sonarr_sync').val() === "Manually") {
                            $('#settings_sonarr_sync_day_div').hide();
                            $('#settings_sonarr_sync_hour_div').hide();
                        } else if ($('#settings_sonarr_sync').val() === "Daily") {
                            $('#settings_sonarr_sync_day_div').hide();
                            $('#settings_sonarr_sync_hour_div').show();
                        } else if ($('#settings_sonarr_sync').val() === "Weekly") {
                            $('#settings_sonarr_sync_day_div').show();
                            $('#settings_sonarr_sync_hour_div').show();
                        }
                    });

                    $('#settings_sonarr_sync').dropdown('clear');
                    $('#settings_sonarr_sync').dropdown('set selected','{{!settings.sonarr.full_update}}');
                    $('#settings_sonarr_sync').dropdown('refresh');
                    $('#settings_sonarr_sync_day').dropdown('clear');
                    $('#settings_sonarr_sync_day').dropdown('set selected','{{!settings.sonarr.full_update_day}}');
                    $('#settings_sonarr_sync_day').dropdown('refresh');
                    $('#settings_sonarr_sync_hour').dropdown('clear');
                    $('#settings_sonarr_sync_hour').dropdown('set selected','{{!settings.sonarr.full_update_hour}}');
                    $('#settings_sonarr_sync_hour').dropdown('refresh');

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
                                $('#sonarr_validation_result').text('Test Successful: Sonarr v' + data.version).css('color', 'green');
                                $('.form').form('validate form');
                                $('#loader').removeClass('active');
                            } else {
                                $('#sonarr_validated').checkbox('uncheck');
                                $('#sonarr_validation_result').text('Test Failed').css('color', 'red');
                                $('.form').form('validate form');
                                $('#loader').removeClass('active');
                            }
                        });
                    });

                    $('.sonarr_config').on('keyup', function() {
                        $('#sonarr_validated').checkbox('uncheck');
                        $('#sonarr_validation_result').text('You Must Test Your Sonarr Connection Settings Before Saving.').css('color', 'red');
                        $('.form').form('validate form');
                        $('#loader').removeClass('active');
                    });

                    $('#settings_sonarr_ssl').on('change', function() {
                        $('#sonarr_validated').checkbox('uncheck');
                        $('#sonarr_validation_result').text('You Must Test Your Sonarr Connection Settings Before Saving.').css('color', 'red');
                        $('.form').form('validate form');
                        $('#loader').removeClass('active');
                    });

                    $("#sonarr_validated").checkbox('check');


                </script>
