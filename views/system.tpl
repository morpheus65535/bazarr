<html>
	<head>
		<!DOCTYPE html>
		<script src="/static/jquery/jquery-latest.min.js"></script>
		<script src="/static/semantic/semantic.min.js"></script>
		<script src="/static/jquery/tablesort.js"></script>
		<link rel="stylesheet" href="/static/semantic/semantic.min.css">
		
		<link rel="apple-touch-icon" sizes="120x120" href="/static/apple-touch-icon.png">
		<link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32x32.png">
		<link rel="icon" type="image/png" sizes="16x16" href="/static/favicon-16x16.png">
		<link rel="manifest" href="/static/manifest.json">
		<link rel="mask-icon" href="/static/safari-pinned-tab.svg" color="#5bbad5">
		<link rel="shortcut icon" href="/static/favicon.ico">
		<meta name="msapplication-config" content="/static/browserconfig.xml">
		<meta name="theme-color" content="#ffffff">
		
		<title>System - Bazarr</title>
		
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
			<div style="background-color:#272727;" class="ui inverted borderless labeled icon huge menu five item">
				<a href="/"><img style="margin-right:32px;" class="logo" src="/static/logo128.png"></a>
				<div style="height:80px;" class="ui container">
					<a class="item" href="/">
						<i class="play icon"></i>
						Series
					</a>
					<a class="item" href="/history">
						<i class="wait icon"></i>
						History
					</a>
					<a class="item" href="/wanted">
						<i class="warning sign icon"></i>
						Wanted
					</a>
					<a class="item" href="/settings">
						<i class="settings icon"></i>
						Settings
					</a>
					<a class="item" href="/system">
						<i class="laptop icon"></i>
						System
					</a>
				</div>
			</div>
		</div>
			
		<div id="fondblanc" class="ui container">
			<div class="ui top attached tabular menu">
				<a class="item active" data-tab="tasks">Tasks</a>
				<a class="item" data-tab="logs">Logs</a>
				<a class="item" data-tab="about">About</a>
			</div>
			<div class="ui bottom attached tab segment active" data-tab="tasks">
				Tasks
			</div>
			<div class="ui bottom attached tab segment" data-tab="logs">
				Logs
			</div>
			<div class="ui bottom attached tab segment" data-tab="about">
				About
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