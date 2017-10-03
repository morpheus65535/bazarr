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
		
		<title>Wanted - Bazarr</title>
		
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
				padding: 3em;
			}
			.fast.backward, .backward, .forward, .fast.forward {
    			cursor: pointer;
			}
		</style>
	</head>
	<body>
		%import ast
		%import pycountry
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
			<table id="tablehistory" class="ui very basic selectable table">
				<thead>
					<tr>
						<th>Series</th>
						<th>Episode</th>
						<th>Episode Title</th>
						<th>Missing subtitles</th>
					</tr>
				</thead>
				<tbody>
				%import time
				%import pretty
				%for row in rows:
					<tr class="selectable">
						<td><a href="/episodes/{{row[4]}}">{{row[0]}}</a></td>
						<td class="collapsing">
							<%episode = row[1].split('x')%>
							{{episode[0] + 'x' + episode[1].zfill(2)}}
						</td>
						<td>{{row[2]}}</td>
						<td>
						%missing_languages = ast.literal_eval(row[3])
						%if missing_languages is not None:
							%for language in missing_languages:
							<a href="/get_subtitle?episodePath={{row[5]}}&language={{pycountry.languages.lookup(str(language)).alpha_3}}&hi={{row[6]}}&sonarrSeriesId={{row[4]}}&sonarrEpisodeId={{row[7]}}" class="ui tiny label">
								{{language}}
								<i style="margin-left:3px; margin-right:0px" class="search icon"></i>
							</a>
							%end
						%end
						</td>
					</tr>
				%end
				</tbody>
			</table>
			<div class="ui grid">
				<div class="three column row">
			    	<div class="column"></div>
			    	<div class="center aligned column">
			    		<i class="\\
			    		%if page == "1":
			    		disabled\\
			    		%end
			    		 fast backward icon"></i>
			    		<i class="\\
			    		%if page == "1":
			    		disabled\\
			    		%end
			    		 backward icon"></i>
			    		{{page}} / {{max_page}}
			    		<i class="\\
			    		%if int(page) == int(max_page):
			    		disabled\\
			    		%end
			    		 forward icon"></i>
			    		<i class="\\
			    		%if int(page) == int(max_page):
			    		disabled\\
			    		%end
			    		 fast forward icon"></i>
			    	</div>
			    	<div class="right floated right aligned column">Total records: {{missing_count}}</div>
				</div>
			</div>
		</div>
	</body>
</html>


<script>
	$('a').click(function(){
		$('#loader').addClass('active');
	})

	$('.fast.backward').click(function(){
		location.href="?page=1";
	})
	$('.backward').click(function(){
		location.href="?page={{int(page)-1}}";
	})
	$('.forward').click(function(){
		location.href="?page={{int(page)+1}}";
	})
	$('.fast.forward').click(function(){
		location.href="?page={{int(max_page)}}";
	})
</script>