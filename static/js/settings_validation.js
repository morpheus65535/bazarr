$('#settings_form')
    .form({
        fields: {
            settings_general_ip	: {
                rules : [
                    {
                        type : 'regExp[/^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/]',
                        prompt : '"General / Start-Up / Listening IP address" must be a valid IPv4 address'
                    },
                    {
                        type : 'empty',
                        prompt : '"General / Start-Up / Listening IP address" must have a value'
                    }
                ]
            },
            settings_general_port : {
                rules : [
                    {
                        type : 'integer[1..65535]',
                        prompt : '"General / Start-Up / Listening port" must be an integer between 1 and 65535'
                    },
                    {
                        type : 'empty',
                        prompt : '"General / Start-Up / Listening port" must have a value'
                    }
                ]
            },
            settings_general_chmod: {
                rules: [
                    {
                        type: 'regExp[^([0-7]{4})$]',
                        prompt : '"General / Start-Up / Set subtitle file permissions to" must be a 4-digit octal (e.g.: 0775)'
                    }
                ]
            },
            settings_auth_password : {
                depends: 'settings_auth_username',
                rules : [
                    {
                        type : 'empty',
                        prompt : '"General / Security settings / Password" must have a value and you must type it again if you change your username.'
                    }
                ]
            },
            sonarr_validated_checkbox : {
                depends: 'settings_general_use_sonarr',
                rules : [
                    {
                        type : 'checked',
                        prompt : '"Sonarr / Connection settings / Test" must be successful before going further'
                    }
                ]
            },
            settings_sonarr_ip : {
                depends: 'settings_general_use_sonarr',
                rules : [
                    {
                        type : 'empty',
                        prompt : '"Sonarr / Connection settings / Hostname or IP address" must have a value'
                    }
                ]
            },
            settings_sonarr_port : {
                depends: 'settings_general_use_sonarr',
                rules : [
                    {
                        type : 'integer[1..65535]',
                        prompt : '"Sonarr / Connection settings / Listening port" must be an integer between 1 and 65535'
                    },
                    {
                        type : 'empty',
                        prompt : '"Sonarr / Connection settings / Listening port" must have a value'
                    }
                ]
            },
//            settings_sonarr_apikey : {
//                depends: 'settings_general_use_sonarr',
//                rules : [
//                    {
//                        type : 'exactLength[32]',
//                        prompt : '"Sonarr / Connection settings / API key" must be exactly {ruleValue} characters'
//                    },
//                    {
//                        type : 'empty',
//                        prompt : '"Sonarr / Connection settings / API key" must have a value'
//                    }
//                ]
//            },
            radarr_validated_checkbox : {
                depends: 'settings_general_use_radarr',
                rules : [
                    {
                        type : 'checked',
                        prompt : '"Radarr / Connection settings / Test" must be successful before going further'
                    }
                ]
            },
            settings_radarr_ip : {
                depends: 'settings_general_use_radarr',
                rules : [
                    {
                        type : 'empty',
                        prompt : '"Radarr / Connection settings / Hostname or IP address" must have a value'
                    }
                ]
            },
            settings_radarr_port : {
                depends: 'settings_general_use_radarr',
                rules : [
                    {
                        type : 'integer[1..65535]',
                        prompt : '"Radarr / Connection settings / Listening port" must be an integer between 1 and 65535'
                    },
                    {
                        type : 'empty',
                        prompt : '"Radarr / Connection settings / Listening port" must have a value'
                    }
                ]
            },
//            settings_radarr_apikey : {
//                depends: 'settings_general_use_radarr',
//                rules : [
//                    {
//                        type : 'exactLength[32]',
//                        prompt : '"Radarr / Connection settings / API key" must be exactly {ruleValue} characters'
//                    },
//                    {
//                        type : 'empty',
//                        prompt : '"Radarr / Connection settings / API key" must have a value'
//                    }
//                ]
//            },
            settings_subliminal_providers : {
                rules : [
                    {
                        type : 'minCount[1]',
                        prompt : '"Subtitles / Subtitles providers" must have at least one enabled provider'
                    }
                ]
            },
            settings_subliminal_languages : {
                rules : [
                    {
                        type : 'minCount[1]',
                        prompt : '"Subtitles / Subtitles languages / Enabled languages" must have at least one enabled language'
                    }
                ]
            },
            settings_days_to_upgrade_subs : {
                depends: 'settings_upgrade_subs',
                rules : [
                    {
                        type : 'integer[1..30]',
                        prompt : '"Subtitles / Subtitles options / Number of days to go back in history..." must be an integer between 1 and 30'
                    }
                ]
            }
        },
        inline : false,
        selector : {
            message: '#form_validation_error'
        },
        on     : 'change',
        onFailure: function(){
            $('.submit').addClass('disabled');
            return false;
        },
        onSuccess: function(){
            $('.submit').removeClass('disabled');
            $('#loader').addClass('active');
        }
    })
;

