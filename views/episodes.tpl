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
		
		<title>{{details[0]}} - Bazarr</title>
		<style>
			body {
				background-color: #1b1c1d;
				background-image: url("/image_proxy{{details[3]}}");
				background-repeat: no-repeat;
				background-attachment: fixed;
				background-size: cover;
				background-position:center center;
			}
			#divmenu {
				background-color: #272727;
				opacity: 0.9;
				padding-top: 2em;
				padding-bottom: 1em;
				padding-left: 1em;
				padding-right: 128px;
			}
			#divdetails {
				background-color: #000000;
				opacity: 0.9;
				color: #ffffff;
				margin-top: 6em;
				margin-bottom: 3em;
				padding: 2em;
				border-radius: 1px;
				box-shadow: 0px 0px 5px 5px #000000;
				min-height: calc(250px + 4em);
			}
			#fondblanc {
				background-color: #ffffff;
				opacity: 0.9;
				border-radius: 1px;
				box-shadow: 0px 0px 3px 3px #ffffff;
				margin-top: 32px;
				margin-bottom: 3em;
				padding-top: 2em;
				padding-left: 2em;
				padding-right: 2em;
				padding-bottom: 1em;
			}
		</style>

		<script>
           	$(document).ready(function(){
            	$('.ui.accordion').accordion();
            	var first_season_acc_title = document.getElementsByClassName("title")[0];
            	first_season_acc_title.className += " active";
            	var first_season_acc_content = document.getElementsByClassName("content")[0];
            	first_season_acc_content.className += " active";
            });

            $(window).on('beforeunload',function(){
			    $('#loader').addClass('active');
			});
		</script>
	</head>
	<body>
		%import ast
		%import pycountry
		%from get_general_settings import *
		<div style="display: none;"><img src="/image_proxy{{details[3]}}"></div>
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
		
		<div style='padding-left: 2em; padding-right: 2em;' class='ui container'>	
			<div id="divdetails" class="ui container">
				<img class="left floated ui image" src="/image_proxy{{details[2]}}">
				<div class="ui right floated inverted basic buttons">
					<button id="scan_disk" class="ui button"><i class="refresh icon"></i>Scan disk for subtitles</button>
					<button id="search_missing_subtitles" class="ui button"><i class="download icon"></i>Download missing subtitles</button>
				</div>
				<h2>{{details[0]}}</h2>
				<p>{{details[1]}}</p>
			</div>

			%if len(seasons) == 0:
				<div id="fondblanc" class="ui container">
					<h2 class="ui header">No episode file available for this series.</h2>
				</div>
			%else:
				%for season in seasons:
				<div id="fondblanc" class="ui container">
					<h1 class="ui header">Season {{season[0][2]}}</h1>
					<div class="ui accordion">
						<div class="title">
							<div class="ui one column stackable center aligned page grid">
								<div class="column twelve wide">
						    	   	<h3 class="ui header"><i class="dropdown icon"></i>
							    	Show/Hide Episodes</h3>
								</div>
							</div>
						</div>
						<div class="content">
							<table class="ui very basic single line selectable table">
								<thead>
									<tr>
										<th class="collapsing">Episode</th>
										<th>Title</th>
										<th class="collapsing">Existing subtitles</th>
										<th class="collapsing">Missing subtitles</th>
									</tr>
								</thead>
								<tbody>
								%for episode in season:
									<tr>
										<td>{{episode[3]}}</td>
										<td>{{episode[0]}}</td>
										<td>
										%actual_languages = ast.literal_eval(episode[4])
										%if actual_languages is not None:
											%for language in actual_languages:
											%if language[1] is not None:
											<a href="/remove_subtitles?episodePath={{episode[1]}}&subtitlesPath={{path_replace(language[1])}}&language={{pycountry.languages.lookup(str(language[0])).alpha_3}}&sonarrSeriesId={{episode[5]}}&sonarrEpisodeId={{episode[7]}}" class="ui tiny label">
												{{language[0]}}
												<i class="delete icon"></i>
											</a>
											%else:
											<div class="ui tiny label">
												{{language[0]}}
											</div>
											%end
											%end
										%end
										</td>
										<td>
										%missing_languages = ast.literal_eval(episode[6])
										%if missing_languages is not None:
											%for language in missing_languages:
											<a href="/get_subtitle?episodePath={{episode[1]}}&language={{pycountry.languages.lookup(str(language)).alpha_3}}&hi={{details[4]}}&sonarrSeriesId={{episode[5]}}&sonarrEpisodeId={{episode[7]}}" class="ui tiny label">
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
						</div>
					</div>
				</div>
			%end
		</div>
	</body>
</html>