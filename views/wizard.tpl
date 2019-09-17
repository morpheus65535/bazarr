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
            <div class="ui indeterminate text loader">Saving Settings...</div>
        </div>

        <div class="ui modal" id="browsemodal">
            <div class="browser"></div>
        </div>

        <div id="fondblanc" class="ui container">
            <form name="wizard_form" id="wizard_form" action="{{base_url}}save_wizard" method="post" class="ui form" autocomplete="off">
            <div id="form_validation_error" class="ui error message">
                <p>Some fields are incorrect and you cannot continue until you have corrected them. Be sure to check every tab.</p>
            </div>
            <div class="ui top attached mini steps">
                <div class="active step" data-tab="general" id="general_tab">
                    <i class="setting icon"></i>
                    <div class="content">
                      <div class="title">General</div>
                      <div class="description">General Settings</div>
                    </div>
                </div>
                <div class="step" data-tab="subtitles" id="subtitles_tab">
                    <i class="closed captioning icon"></i>
                    <div class="content">
                      <div class="title">Subtitles</div>
                      <div class="description">Subtitles Settings</div>
                    </div>
                </div>
                <div class="step" data-tab="sonarr" id="sonarr_tab">
                    <i class="play icon"></i>
                    <div class="content">
                      <div class="title">Sonarr</div>
                      <div class="description">Sonarr Settings</div>
                    </div>
                </div>
                <div class="step" data-tab="radarr" id="radarr_tab">
                    <i class="film icon"></i>
                    <div class="content">
                      <div class="title">Radarr</div>
                      <div class="description">Radarr Settings</div>
                    </div>
                </div>
            </div>
            <div class="ui bottom attached tab segment active" data-tab="general" id="general">
                <div class="ui container"><button class="submit ui blue right floated right labeled icon button next1">
                    <i class="right arrow icon"></i>
                    Next
                </button></div>

                % include('wizard_general.tpl')
            </div>
            <div class="ui bottom attached tab segment" data-tab="subtitles" id="subtitles">

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

            % include('wizard_subtitles')
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

                % include('wizard_sonarr.tpl')
            </div>
            <div class="ui bottom attached tab segment" data-tab="radarr" id="radarr">

                <div class="ui container"><button class="submit ui blue right floated lright labeled icon button" id="submit" type="submit" value="Submit" form="wizard_form"><i class="save icon"></i>Save</button>
                <button class="submit ui blue right floated left labeled icon button prev3">
                    <i class="left arrow icon"></i>
                    Prev
                </button></div>

                % include('wizard_radarr')
            </div>
            </form>
        </div>
        % include('footer.tpl')
    </body>
</html>

<script src="{{base_url}}static/js/wizard_validation.js"></script>

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
            $('#subtitles').addClass('active');
            $('#subtitles_tab').addClass('active');
            $('#general_tab').removeClass('active');
            $('#general_tab').addClass('completed');
        });

        $('.prev1').on('click', function(m) {
            m.preventDefault();

            $('#general').addClass('active');
            $('#subtitles').removeClass('active');
            $('#subtitles_tab').removeClass('active');
            $('#general_tab').removeClass('completed');
            $('#general_tab').addClass('active');
        });

        $('.next2').on('click', function(e) {
            e.preventDefault();

            $('#subtitles').removeClass('active');
            $('#sonarr').addClass('active');
            $('#sonarr_tab').addClass('active');
            $('#subtitles_tab').removeClass('active');
            $('#subtitles_tab').addClass('completed');
        });

        $('.prev2').on('click', function(m) {
            m.preventDefault();

            $('#subtitles').addClass('active');
            $('#sonarr').removeClass('active');
            $('#sonarr_tab').removeClass('active');
            $('#subtitles_tab').removeClass('completed');
            $('#subtitles_tab').addClass('active');
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

    $(function() {
        $('.form').form('validate form');
        $('#loader').removeClass('active');
    });

    $(".form :input").on('change paste keyup focusout', function() {
       $('.form').form('validate form');
        $('#loader').removeClass('active');
    });
</script>
