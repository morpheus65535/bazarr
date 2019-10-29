                <div class="ui dividing header">Notifications settings</div>
                <div class="twelve wide column">
                    <div class="ui info message">
                        <p>Thanks to caronc for his work on <a href="https://github.com/caronc/apprise" target="_blank">apprise</a>, which is based the notifications system.</p>
                    </div>
                    <div class="ui info message">
                        <p>Please follow instructions on his <a href="https://github.com/caronc/apprise/wiki" target="_blank">Wiki</a> to configure your notification providers.</p>
                    </div>
                    <div class="ui grid">
                        %for notifier in settings_notifier:
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>{{notifier['name']}}</label>
                            </div>
                            <div class="one wide column">
                                <div id="settings_notifier_{{notifier['name']}}_enabled" class="notifier_enabled ui toggle checkbox" data-notifier-url-div="settings_notifier_{{notifier['name']}}_url_div" data-enabled={{notifier['enabled']}}>
                                    <input name="settings_notifier_{{notifier['name']}}_enabled" type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="eight wide column">
                                <div class='field'>
                                    <div id="settings_notifier_{{notifier['name']}}_url_div" class="ui fluid input">
                                        <input name="settings_notifier_{{notifier['name']}}_url" type="text" value="{{notifier['url'] if notifier['url'] != None else ''}}">
                                        <div class="test_notification ui blue button" data-notification="{{notifier['url']}}">Test Notification</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        %end
                    </div>
                </div>

                <script>
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



                </script>
