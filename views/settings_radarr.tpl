                <div class="ui dividing header">Connection settings</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Settings Validation:</label>
                            </div>
                            <div class="two wide column">
                                <button id="radarr_validate" class="test ui blue button" type="button">
                                    Test
                                </button>
                            </div>
                            <div class="seven wide column">
                                <div id="radarr_validated" class="ui read-only checkbox">
                                    <input id="radarr_validated_checkbox" type="checkbox">
                                    <label id="radarr_validation_result">Not Tested Recently</label>
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
                                <label>Listening Port</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_radarr_port" name="settings_radarr_port" type="text" class="radarr_config" value="{{settings.radarr.port}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="TCP Port of Radarr" data-inverted="">
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
                                <label>SSL Enabled</label>
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
                                <label>API Key</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_radarr_apikey" name="settings_radarr_apikey" type="text" class="radarr_config" value="{{settings.radarr.apikey}}">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="API Key for Radarr (32 alphanumeric characters)" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Download Only Monitored</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_only_monitored_radarr" class="ui toggle checkbox" data-monitored={{settings.radarr.getboolean('only_monitored')}}>
                                    <input name="settings_radarr_only_monitored" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Automatic download of Subtitles will only happen for monitored Movies in Radarr." data-inverted="">
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
                                    <select name="settings_radarr_sync" id="settings_radarr_sync" class="ui fluid selection dropdown">
                                        <option value="Manually">Manually</option>
                                        <option value="Daily">Daily</option>
                                        <option value="Weekly">Weekly</option>
                                    </select>
                                </div>
                            </div>
                            <div id="settings_radarr_sync_day_div" class="three wide column">
                                <div class='field'>
                                    <select name="settings_radarr_sync_day" id="settings_radarr_sync_day" class="ui fluid selection dropdown">
                                        % import calendar
                                        % for idx, i in enumerate(calendar.day_name):
                                        <option value="{{idx}}">{{i}}</option>
                                        %end
                                    </select>
                                </div>
                            </div>
                            <div id="settings_radarr_sync_hour_div" class="two wide column">
                                <div class='field'>
                                    <select name="settings_radarr_sync_hour" id="settings_radarr_sync_hour" class="ui fluid selection dropdown">
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
                    if ($('#radarr_ssl_div').data("ssl") === "True") {
                        $("#radarr_ssl_div").checkbox('check');
                    } else {
                        $("#radarr_ssl_div").checkbox('uncheck');
                    }

                    if ($('#settings_only_monitored_radarr').data("monitored") === "True") {
                        $("#settings_only_monitored_radarr").checkbox('check');
                    } else {
                        $("#settings_only_monitored_radarr").checkbox('uncheck');
                    }

                    $('#settings_radarr_sync').dropdown('setting', 'onChange', function(){
                        if ($('#settings_radarr_sync').val() === "Manually") {
                            $('#settings_radarr_sync_day_div').hide();
                            $('#settings_radarr_sync_hour_div').hide();
                        } else if ($('#settings_radarr_sync').val() === "Daily") {
                            $('#settings_radarr_sync_day_div').hide();
                            $('#settings_radarr_sync_hour_div').show();
                        } else if ($('#settings_radarr_sync').val() === "Weekly") {
                            $('#settings_radarr_sync_day_div').show();
                            $('#settings_radarr_sync_hour_div').show();
                        }
                    });

                    $('#settings_radarr_sync').dropdown('clear');
                    $('#settings_radarr_sync').dropdown('set selected','{{!settings.radarr.full_update}}');
                    $('#settings_radarr_sync').dropdown('refresh');
                    $('#settings_radarr_sync_day').dropdown('clear');
                    $('#settings_radarr_sync_day').dropdown('set selected','{{!settings.radarr.full_update_day}}');
                    $('#settings_radarr_sync_day').dropdown('refresh');
                    $('#settings_radarr_sync_hour').dropdown('clear');
                    $('#settings_radarr_sync_hour').dropdown('set selected','{{!settings.radarr.full_update_hour}}');
                    $('#settings_radarr_sync_hour').dropdown('refresh');

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
                        $('#radarr_validation_result').text('You Must Test Your Radarr Connection Settings Before Saving.').css('color', 'red');
                        $('.form').form('validate form');
                        $('#loader').removeClass('active');
                    });

                    $('#settings_radarr_ssl').on('change', function() {
                        $('#radarr_validated').checkbox('uncheck');
                        $('#radarr_validation_result').text('You Must Test Your Radarr Connection Settings Before Saving.').css('color', 'red');
                        $('.form').form('validate form');
                        $('#loader').removeClass('active');
                    });

                    $("#radarr_validated").checkbox('check');
                </script>
