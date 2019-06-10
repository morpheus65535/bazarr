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
                <a class="tabs item" data-tab="subtitles">Subtitles</a>
                <a class="tabs item" data-tab="notifier">Notifications</a>
            </div>
            <div class="ui bottom attached tab segment active" data-tab="general">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
                % include('settings_general.tpl')
            </div>
            <div class="ui bottom attached tab segment" data-tab="sonarr">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
                % include('settings_sonarr.tpl')
            </div>
            <div class="ui bottom attached tab segment" data-tab="radarr">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
                % include('settings_radarr.tpl')
            </div>
            <div class="ui bottom attached tab segment" data-tab="subtitles">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
                % include('settings_subtitles.tpl')
            </div>
            <div class="ui bottom attached tab segment" data-tab="notifier">
                <div class="ui container"><button class="submit ui blue right floated button" type="submit" value="Submit" form="settings_form">Save</button></div>
                % include('settings_notifications.tpl')
            </div>
            </form>
        </div>
        % include('footer.tpl')
    </body>
</html>

<script src="{{base_url}}static/js/settings_validation.js"></script>

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

    $('.menu .item')
        .tab()
    ;

    $('a:not(.tabs), button:not(.cancel, .test)').on('click', function(){
        $('#loader').addClass('active');
    });

    $('a[target="_blank"]').on('click', function(){
        $('#loader').removeClass('active');
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

<script>
    // Don't move this part to settings_general.tpl as #settings_form is undefined in this template
    if ($('#settings_proxy_type').val() === "None") {
        $('.proxy_option').hide();
        $('#settings_form').form('remove rule', 'settings_proxy_url', 'empty');
        $('#settings_form').form('remove rule', 'settings_proxy_port', 'empty');
        $('#settings_form').form('remove rule', 'settings_proxy_port', 'integer[1..65535]');
    } else {
        $('#settings_form').form('add rule', 'settings_proxy_url', {rules: [{type : 'empty', prompt : '"General / Proxy settings / Hostname" must have a value'}]});
        $('#settings_form').form('add rule', 'settings_proxy_port', {rules: [{type : 'empty', prompt : '"General / Proxy settings / Port" must have a value'}]});
        $('#settings_form').form('add rule', 'settings_proxy_port', {rules: [{type : 'integer[1..65535]', prompt : '"General / Proxy settings / Port" must be an integer between 1 and 65535'}]});
    }

    // Don't move this part to settings_general.tpl as #settings_form is undefined in this template
    $('#settings_proxy_type').dropdown('setting', 'onChange', function(){
        if ($('#settings_proxy_type').val() === "None") {
            $('.proxy_option').hide();
            $('#settings_form').form('remove rule', 'settings_proxy_url', 'empty');
            $('#settings_form').form('remove rule', 'settings_proxy_port', 'empty');
            $('#settings_form').form('remove rule', 'settings_proxy_port', 'integer[1..65535]');
            $('.form').form('validate form');
            $('#loader').removeClass('active');
        } else {
            $('.proxy_option').show();
            $('#settings_form').form('add rule', 'settings_proxy_url', {rules: [{type : 'empty', prompt : '"General / Proxy settings / Hostname" must have a value'}]});
            $('#settings_form').form('add rule', 'settings_proxy_port', {rules: [{type : 'empty', prompt : '"General / Proxy settings / Port" must have a value'}]});
            $('#settings_form').form('add rule', 'settings_proxy_port', {rules: [{type : 'integer[1..65535]', prompt : '"General / Proxy settings / Port" must be an integer between 1 and 65535'}]});
            $('.form').form('validate form');
            $('#loader').removeClass('active');
        }
    });
</script>
