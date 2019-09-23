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
                                    <div class="ui basic icon" data-tooltip="Enable Radarr Integration." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="radarr_hide middle aligned row">
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
                                <div class="ui basic icon" data-tooltip="Hostname or IP4 Address of Radarr" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="radarr_hide middle aligned row">
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
                                <label>SSL Enabled</label>
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
                                <label>API Key</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <input id="settings_radarr_apikey" name="settings_radarr_apikey" type="text" class="radarr_config">
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed center aligned column">
                                <div class="ui basic icon" data-tooltip="API Key for Radarr (32 alphanumeric characters)" data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>

                        <div class="radarr_hide middle aligned row">
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
                                <div class="ui basic icon" data-tooltip="Only Download Subtitles For Monitored Movies in Radarr." data-inverted="">
                                    <i class="help circle large icon"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                    </div>
                </div>

                <script>
                    $(".radarr_hide").hide();
                    $('#settings_use_radarr').checkbox({
                        onChecked: function() {
                            $(".radarr_hide").show();
                        },
                        onUnchecked: function() {
                            $(".radarr_hide").hide();
                        }
                    });

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
                                $('#radarr_validation_result').text('Test Failed').css('color', 'red');
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
