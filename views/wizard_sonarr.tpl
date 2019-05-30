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

                <script>
                    $(".sonarr_hide").hide();
                    $('#settings_use_sonarr').checkbox({
                        onChecked: function() {
                            $(".sonarr_hide").show();
                        },
                        onUnchecked: function() {
                            $(".sonarr_hide").hide();
                        }
                    });

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
                </script>