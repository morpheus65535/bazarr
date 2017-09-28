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
		
		<title>History - Bazarr</title>
		
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
			}
			#tablehistory {
				padding: 3em;
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
					<a class="item" href="/">
						<i class="play icon"></i>
						Series
					</a>
					<a class="item" href="/history">
						<i class="wait icon"></i>
						History
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
			<table id="tablehistory" class="ui very basic selectable table">
				<thead>
					<tr>
						<th></th>
						<th>Series</th>
						<th>Episode</th>
						<th>Episode Title</th>
						<th>Date</th>
						<th>Description</th>
					</tr>
				</thead>
				<tbody>
				%import time
				%import pretty
				%for row in rows:
					<tr class="selectable">
						<td class="collapsing">
						%if row[0] == 0:
							<div class="ui inverted basic compact icon" data-tooltip="Subtitles file have been erased." data-inverted="">
								<i class="ui trash icon"></i>
							</div>
						%elif row[0] == 1:
							<div class="ui inverted basic compact icon" data-tooltip="Subtitles file have been downloaded." data-inverted="">
								<i class="ui download icon"></i>
							</div>
						%end
						</td>
						<td><a href="/episodes/{{row[6]}}">{{row[1]}}</a></td>
						<td class="collapsing">
							<%episode = row[2].split('x')%>
							{{episode[0] + 'x' + episode[1].zfill(2)}}
						</td>
						<td>{{row[3]}}</td>
						<td class="collapsing">
							<div class="ui inverted" data-tooltip="{{time.strftime('%A, %B %d %Y %H:%M', time.localtime(row[4]))}}" data-inverted="">
								{{pretty.date(int(row[4]))}}
							</div>
						</td>
						<td>{{row[5]}}</td>
					</tr>
				%end
				</tbody>
			</table>
		</div>
	</body>
</html>


<script>
	$('a').click(function(){
		$('#loader').addClass('active');
	})
</script>