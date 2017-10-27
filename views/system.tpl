<html>
	<head>
		<!DOCTYPE html>
		<script src="{{base_url}}/static/jquery/jquery-latest.min.js"></script>
		<script src="{{base_url}}/static/semantic/semantic.min.js"></script>
		<script src="{{base_url}}/static/jquery/tablesort.js"></script>
		<link rel="stylesheet" href="{{base_url}}/static/semantic/semantic.min.css">
		
		<link rel="apple-touch-icon" sizes="120x120" href="{{base_url}}/static/apple-touch-icon.png">
		<link rel="icon" type="image/png" sizes="32x32" href="{{base_url}}/static/favicon-32x32.png">
		<link rel="icon" type="image/png" sizes="16x16" href="{{base_url}}/static/favicon-16x16.png">
		<link rel="manifest" href="{{base_url}}/static/manifest.json">
		<link rel="mask-icon" href="{{base_url}}/static/safari-pinned-tab.svg" color="#5bbad5">
		<link rel="shortcut icon" href="{{base_url}}/static/favicon.ico">
		<meta name="msapplication-config" content="{{base_url}}/static/browserconfig.xml">
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
				margin-bottom: 3em;
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
				<a href="{{base_url}}/"><img style="margin-right:32px;" class="logo" src="{{base_url}}/static/logo128.png"></a>
				<div style="height:80px;" class="ui container">
					<a class="item" href="{{base_url}}/">
						<i class="play icon"></i>
						Series
					</a>
					<a class="item" href="{{base_url}}/history">
						<i class="wait icon"></i>
						History
					</a>
					<a class="item" href="{{base_url}}/wanted">
						<i class="warning sign icon"></i>
						Wanted
					</a>
					<a class="item" href="{{base_url}}/settings">
						<i class="settings icon"></i>
						Settings
					</a>
					<a class="item" href="{{base_url}}/system">
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
				<div class="content">
					<table class="ui very basic selectable table">
						<thead>
							<tr>
								<th>Name</th>
								<th>Interval</th>
								<th>Next Execution</th>
							</tr>
						</thead>
						<tbody>
						%for task in task_list:
							<tr>
								<td>{{task[0]}}</td>
								<td>{{task[1]}}</td>
								<td>{{task[2]}}</td>
							</tr>
						%end
						</tbody>
					</table>
				</div>
			</div>
			<div class="ui bottom attached tab segment" data-tab="logs">
				<div class="content">
					<table class="ui very basic selectable table">
						<thead>
							<tr>
								<th class="collapsing"></th>
								<th>Message</th>
								<th class="collapsing">Time</th>
							</tr>
						</thead>
						<tbody>
						%import time
						%import datetime
						%import pretty
						%for log in logs:
							%line = []
							%line = log.split('|')
							<tr class='log' data-message='{{line[2]}}' data-exception='{{line[3].replace("\\n", "<br />")}}'>
								<td class="collapsing"><i class="\\
								%if line[1] == 'INFO':
blue info circle \\
								%elif line[1] == 'WARNING':
yellow warning circle \\
								%elif line[1] == 'ERROR':
red bug \\
								%end
icon"></i></td>
								<td>{{line[2]}}</td>
								<td title='{{line[0]}}' class="collapsing">{{pretty.date(int(time.mktime(datetime.datetime.strptime(line[0], "%d/%m/%Y %H:%M:%S").timetuple())))}}</td>
							</tr>
						%end
						</tbody>
					</table>
				</div>
			</div>
			<div class="ui bottom attached tab segment" data-tab="about">
				About
			</div>
		</div>

		<div class="ui small modal">
			<i class="close icon"></i>
			<div class="header">
				<div>Details</div>
			</div>
			<div class="content">
				Message
				<div id='message' class="ui segment">
					<p></p>
				</div>
				Exception
				<div id='exception' class="ui segment">
					<p></p>
				</div>
			</div>
			<div class="actions">
				<button class="ui cancel button" >Close</button>
			</div>
		</div>
	</body>
</html>


<script>
	$('.modal')
		.modal({
	    	autofocus: false
		})
	;

	$('.menu .item')
		.tab()
	;

	$('.log').click(function(){
		$("#message").html($(this).data("message"));
		$("#exception").html($(this).data("exception"));
		$('.small.modal').modal('show');
	})

	$('a, button:not(.cancel)').click(function(){
		$('#loader').addClass('active');
	})
</script>