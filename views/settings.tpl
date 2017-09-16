<html>
	<head>
		<!DOCTYPE html>
		<script src="https://code.jquery.com/jquery-latest.min.js"></script>
		<script src="https://cdn.jsdelivr.net/semantic-ui/latest/semantic.min.js"></script>
		<script src="https://semantic-ui.com/javascript/library/tablesort.js"></script>
		<link rel="stylesheet" href="https://cdn.jsdelivr.net/semantic-ui/latest/semantic.min.css">
		
		<link rel="apple-touch-icon" sizes="120x120" href="/static/apple-touch-icon.png">
		<link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32x32.png">
		<link rel="icon" type="image/png" sizes="16x16" href="/static/favicon-16x16.png">
		<link rel="manifest" href="/static/manifest.json">
		<link rel="mask-icon" href="/static/safari-pinned-tab.svg" color="#5bbad5">
		<link rel="shortcut icon" href="/static/favicon.ico">
		<meta name="msapplication-config" content="/static/browserconfig.xml">
		<meta name="theme-color" content="#ffffff">
		
		<title>Settings - Bazarr</title>
		
		<style>
			body {
				background-color: #272727;
			}
			#divmenu {
				background-color: #272727;
				opacity: 0.9;
				padding-top: 2em;
				padding-bottom: 1em;
				padding-left: 1em;
				padding-right: 128px;
			}
			#fondblanc {
				background-color: #ffffff;
				border-radius: 0px;
				box-shadow: 0px 0px 5px 5px #ffffff;
				margin-top: 32px;
				padding: 1em;
			}
		</style>
	</head>
	<body>
		<div id='loader' class="ui page dimmer">
		   	<div class="ui indeterminate text loader">Loading...</div>
		</div>
		<div id="divmenu" class="ui container">
			<div style="background-color:#272727;" class="ui inverted borderless labeled icon huge menu four item">
				<a href="/"><img style="margin-right:32px;" class="logo" src="/static/logo128.png"></a>
				<div style="height:80px;" class="ui container">
					<a class="menu item" href="/">
						<i class="play icon"></i>
						Series
					</a>
					<a class="menu item" href="/history">
						<i class="wait icon"></i>
						History
					</a>
					<a class="menu item" href="/settings">
						<i class="settings icon"></i>
						Settings
					</a>
					<a class="menu item" href="/system">
						<i class="laptop icon"></i>
						System
					</a>
				</div>
			</div>
		</div>
			
		<div id="fondblanc" class="ui container">
			<div class="ui top attached tabular menu">
				<a class="item active" data-tab="general">General</a>
				<a class="item" data-tab="sonarr">Sonarr</a>
				<a class="item" data-tab="subliminal">Subliminal</a>
				<a class="item" data-tab="providers">Providers</a>
				<a class="item" data-tab="languages">Languages</a>
			</div>
			<div class="ui bottom attached tab segment active" data-tab="general">
				General
			</div>
			<div class="ui bottom attached tab segment" data-tab="sonarr">
				Sonarr
			</div>
			<div class="ui bottom attached tab segment" data-tab="subliminal">
				Subliminal
			</div>
			<div class="ui bottom attached tab segment" data-tab="providers">
				Providers
			</div>
			<div class="ui bottom attached tab segment" data-tab="languages">
				Languages
			</div>
		</div>
	</body>
</html>


<script>
	$('.menu .item')
		.tab()
	;

	$('a.menu').click(function(){
		$('#loader').addClass('active');
	})
</script>