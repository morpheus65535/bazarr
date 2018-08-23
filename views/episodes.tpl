<html>
	<head>
		<!DOCTYPE html>
		<script src="{{base_url}}static/jquery/jquery-latest.min.js"></script>
		<script src="{{base_url}}static/semantic/semantic.min.js"></script>
		<script src="{{base_url}}static/jquery/tablesort.js"></script>
		<script src="{{base_url}}static/datatables/jquery.dataTables.min.js"></script>
		<script src="{{base_url}}static/datatables/dataTables.semanticui.min.js"></script>
		<link rel="stylesheet" href="{{base_url}}static/semantic/semantic.css">
		<link rel="stylesheet" type="text/css" href="{{base_url}}static/datatables/datatables.min.css"/>
		<link rel="stylesheet" type="text/css" href="{{base_url}}static/datatables/semanticui.min.css"/>

		
		<link rel="apple-touch-icon" sizes="120x120" href="{{base_url}}static/apple-touch-icon.png">
		<link rel="icon" type="image/png" sizes="32x32" href="{{base_url}}static/favicon-32x32.png">
		<link rel="icon" type="image/png" sizes="16x16" href="{{base_url}}static/favicon-16x16.png">
		<link rel="manifest" href="{{base_url}}static/manifest.json">
		<link rel="mask-icon" href="{{base_url}}static/safari-pinned-tab.svg" color="#5bbad5">
		<link rel="shortcut icon" href="{{base_url}}static/favicon.ico">
		<meta name="msapplication-config" content="{{base_url}}static/browserconfig.xml">
		<meta name="theme-color" content="#ffffff">
		
		<title>{{details[0]}} - Bazarr</title>
		<style>
			body {
				background-color: #1b1c1d;
				background-image: url("{{base_url}}image_proxy{{details[3]}}");
				background-repeat: no-repeat;
				background-attachment: fixed;
				background-size: cover;
				background-position:center center;
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
			.ui.basic.button:hover, .ui.basic.buttons .button:hover {
				background: transparent !important;
			}
			.ui.basic.button:active, .ui.basic.buttons .button:active {
				background: transparent !important;
			}
			.ui.basic.button:focus, .ui.basic.buttons .button:focus {
				background: transparent !important;
			}
			.ui.basic.button:visited, .ui.basic.buttons .button:visited {
				background: transparent !important;
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
		</script>
	</head>
	<body>
		%import ast
		%from get_languages import *
		%from get_general_settings import *
		%single_language = get_general_settings()[7]
		<div style="display: none;"><img src="{{base_url}}image_proxy{{details[3]}}"></div>
		<div id='loader' class="ui page dimmer">
		   	<div class="ui indeterminate text loader">Loading...</div>
		</div>
		% include('menu.tpl')
		
		<div style='padding-left: 2em; padding-right: 2em;' class='ui container'>	
			<div id="divdetails" class="ui container">
				<img class="left floated ui image" style="max-height:250px;" src="{{base_url}}image_proxy{{details[2]}}">
				<div class="ui right floated basic icon buttons">
					<button id="scan_disk" class="ui button" data-tooltip="Scan disk for subtitles" data-inverted=""><i class="ui inverted large compact refresh icon"></i></button>
					<button id="search_missing_subtitles" class="ui button" data-tooltip="Download missing subtitles" data-inverted=""><i class="ui inverted huge compact search icon"></i></button>
					<%
					subs_languages = ast.literal_eval(str(details[7]))
					subs_languages_list = []
					if subs_languages is not None:
						for subs_language in subs_languages:
							subs_languages_list.append(subs_language)
						end
					end
					%>
					<button id="config" class="ui button" data-tooltip="Edit series" data-inverted="" data-tvdbid="{{details[5]}}" data-title="{{details[0]}}" data-poster="{{details[2]}}" data-audio="{{details[6]}}" data-languages="{{!subs_languages_list}}" data-hearing-impaired="{{details[4]}}"><i class="ui inverted large compact configure icon"></i></button>
				</div>
				<h2>{{details[0]}}</h2>
				<p>{{details[1]}}</p>
				<p style='margin-top: 3em;'>
					<div class="ui tiny inverted label" style='background-color: #777777;'>{{details[6]}}</div>
					<div class="ui tiny inverted label" style='background-color: #35c5f4;'>{{details[8]}}</div>
					<div class="ui tiny inverted label" style='background-color: #35c5f4;'>{{number}} files</div>
				</p>
				<p style='margin-top: 2em;'>
					%for language in subs_languages_list:
                    <div class="ui tiny inverted label" style='background-color: #35c5f4;'>{{language}}</div>
					%end
				</p>
				<div style='clear:both;'></div>
			</div>

			%if len(seasons) == 0:
				<div id="fondblanc" class="ui container">
					<h3 class="ui header">No episode files available for this series or Bazarr is still synchronizing with Sonarr. Please come back later.</h3>
				</div>
			%else:
				%for season in seasons:
				<div id="fondblanc" class="ui container">
					%missing_subs = len([i for i in season if i[6] != "[]"])
					%total_subs = len(season)
					%subs_label = ''
					%if subs_languages is not None:
					%	subs_label = '<div class="ui tiny '
					%	if missing_subs == 0:
					%		subs_label = subs_label + 'green'
					%	else:
					%		subs_label = subs_label + 'yellow'
					%	end
					%	subs_label = subs_label + ' circular label">' + str(total_subs - missing_subs) + ' / ' + str(total_subs) + '</div>'
					%end
					<h1 class="ui header">Season {{season[0][2]}}{{!subs_label}}</h1>
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
										<th class="collapsing"></th>
										<th class="collapsing">Episode</th>
										<th>Title</th>
										<th class="collapsing">Existing<br>subtitles</th>
										<th class="collapsing">Missing<br>subtitles</th>
										<th class="collapsing">Manual<br>search</th>
									</tr>
								</thead>
								<tbody>
								%for episode in season:
									<tr>
										<td class="collapsing">
                                            %if episode[9] == "True":
                                            <span data-tooltip="Episode monitored in Sonarr"><i class="bookmark icon"></i></span>
                                            %else:
                                            <span data-tooltip="Episode unmonitored in Sonarr"><i class="bookmark outline icon"></i></span>
                                            %end
                                        </td>
										<td>{{episode[3]}}</td>
										<td>{{episode[0]}}</td>
										<td>
										%if episode[4] is not None:
										%	actual_languages = ast.literal_eval(episode[4])
                                        %   actual_languages.sort()
										%else:
										%	actual_languages = '[]'
										%end
										%try:
											%for language in actual_languages:
												%if language[1] is not None:
												<a data-episodePath="{{episode[1]}}" data-subtitlesPath="{{path_replace(language[1])}}" data-language="{{alpha3_from_alpha2(str(language[0]))}}" data-sonarrSeriesId={{episode[5]}} data-sonarrEpisodeId={{episode[7]}} class="remove_subtitles ui tiny label">
													{{language[0]}}
													<i class="delete icon"></i>
												</a>
												%else:
												<div class="ui tiny label">
													{{language[0]}}
												</div>
												%end
											%end
										%except:
											%pass
										%end
										</td>
										<td>
										%try:
											%if episode[6] is not None:
											%	missing_languages = ast.literal_eval(episode[6])
                                            %   missing_languages.sort()
											%else:
											%	missing_languages = None
											%end
											%if missing_languages is not None:
                                                %for language in missing_languages:
                                                <a data-episodePath="{{episode[1]}}" data-scenename="{{episode[8]}}" data-language="{{alpha3_from_alpha2(str(language))}}" data-hi="{{details[4]}}" data-sonarrSeriesId={{episode[5]}} data-sonarrEpisodeId={{episode[7]}} class="get_subtitle ui tiny label">
													{{language}}
													<i style="margin-left:3px; margin-right:0px" class="search icon"></i>
												</a>
												%end
											%end
										%except:
											%pass
										%end
										</td>
										<td>
											<a data-episodePath="{{episode[1]}}" data-scenename="{{episode[8]}}" data-language="{{subs_languages_list}}" data-hi="{{details[4]}}" data-series_title="{{details[0]}}" data-season="{{episode[2]}}" data-episode="{{episode[3]}}" data-episode_title="{{episode[0]}}" class="manual_search ui tiny label"><i class="ui user icon" style="margin-right:0px" ></i></a>
										</td>
									</tr>
								%end
								</tbody>
							</table>
						</div>
					</div>
				</div>
				%end
			%end
		</div>

		<div class="config_dialog ui small modal">
			<i class="close icon"></i>
			<div class="header">
				<div id="series_title"></div>
			</div>
			<div class="content">
				<form name="series_form" id="series_form" action="" method="post" class="ui form">
					<div class="ui grid">
						<div class="four wide column">
							<img id="series_poster" class="ui image" src="">
						</div>
						<div class="twelve wide column">
							<div class="ui grid">
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Audio language</label>
									</div>
									<div class="nine wide column">
										<div id="series_audio_language"></div>
									</div>
								</div>
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Subtitles languages</label>
									</div>
									<div class="nine wide column">
										<select name="languages" id="series_languages" {{!'multiple="" ' if single_language == 'False' else ''}} class="ui fluid selection dropdown">
											<option value="">Languages</option>
										    %if single_language == 'True':
                                            <option value="None">None</option>
                                            %end
											%for language in languages:
											<option value="{{language[0]}}">{{language[1]}}</option>
											%end
										</select>
									</div>
								</div>
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Hearing-impaired</label>
									</div>
									<div class="nine wide column">
										<div id="series_hearing-impaired_div" class="ui toggle checkbox">
											<input name="hearing_impaired" id="series_hearing-impaired" type="checkbox">
											<label></label>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</form>
			</div>
			<div class="actions">
				<button class="ui cancel button" >Cancel</button>
				<button type="submit" name="save" value="save" form="series_form" class="ui blue approve button">Save</button>
			</div>
		</div>

		<div class="search_dialog ui modal">
			<i class="close icon"></i>
			<div class="header">
				<span id="series_title_span"></span> - <span id="season"></span>x<span id="episode"></span> - <span id="episode_title"></span>
			</div>
			<div class="scrolling content">
				<table id="search_result" class="display" style="width:100%">
					<thead>
						<tr>
							<th>Score</th>
							<th>Hearing-impaired</th>
							<th>Provider</th>
						</tr>
					</thead>
				</table>
			</div>
			<div class="actions">
				<button class="ui cancel button" >Cancel</button>
			</div>
		</div>

		% include('footer.tpl')
	</body>
</html>

<script>
	$('#scan_disk').click(function(){
		window.location = '{{base_url}}scan_disk/{{no}}';
	})

	$('#search_missing_subtitles').click(function(){
		window.location = '{{base_url}}search_missing_subtitles/{{no}}';
	})

	$('.remove_subtitles').click(function(){
		var values = {
				episodePath: $(this).attr("data-episodePath"),
				language: $(this).attr("data-language"),
				subtitlesPath: $(this).attr("data-subtitlesPath"),
				sonarrSeriesId: $(this).attr("data-sonarrSeriesId"),
				sonarrEpisodeId: $(this).attr("data-sonarrEpisodeId"),
				tvdbid: {{tvdbid}}
		};
		$.ajax({
			url: "{{base_url}}remove_subtitles",
			type: "POST",
			dataType: "json",
			data: values
		});
		$(document).ajaxStart(function(){
			$('#loader').addClass('active');
		});
		$(document).ajaxStop(function(){
			window.location.reload();
		});
	})

	$('.get_subtitle').click(function(){
		var values = {
				episodePath: $(this).attr("data-episodePath"),
				sceneName: $(this).attr("data-sceneName"),
				language: $(this).attr("data-language"),
				hi: $(this).attr("data-hi")
		};
		$.ajax({
			url: "{{base_url}}get_subtitle",
			type: "POST",
			dataType: "json",
			data: values
		});
		$(document).ajaxStart(function(){
			$('#loader').addClass('active');
		});
		$(document).ajaxStop(function(){
			window.location.reload();
		});
	})

	$('a:not(.manual_search), .menu .item, button:not(#config, .cancel)').click(function(){
		$('#loader').addClass('active');
	})

	$('.modal')
		.modal({
			autofocus: false
		})
	;

	$('#config').click(function(){
		$('#series_form').attr('action', '{{base_url}}edit_series/{{no}}');

		$("#series_title").html($(this).data("title"));
		$("#series_poster").attr("src", "{{base_url}}image_proxy" + $(this).data("poster"));

		$("#series_audio_language").html($(this).data("audio"));

		$('#series_languages').dropdown('clear');
		var languages_array = eval($(this).data("languages"));
		$('#series_languages').dropdown('set selected',languages_array);

		if ($(this).data("hearing-impaired") == "True") {
			$("#series_hearing-impaired_div").checkbox('check');
		} else {
			$("#series_hearing-impaired_div").checkbox('uncheck');
		}

		$('.config_dialog')
			.modal({
				centered: true
			})
			.modal('show')
		;
	})

	$('.manual_search').click(function(){
		$("#series_title_span").html($(this).data("series_title"));
		$("#season").html($(this).data("season"));
		$("#episode").html($(this).data("episode"));
		$("#episode_title").html($(this).data("episode_title"));

		var values = {
			episodePath: $(this).attr("data-episodePath"),
			sceneName: $(this).attr("data-sceneName"),
			language: $(this).attr("data-language"),
			hi: $(this).attr("data-hi"),
			sonarrSeriesId: $(this).attr("data-sonarrSeriesId"),
			sonarrEpisodeId: $(this).attr("data-sonarrEpisodeId"),
			tvdbid: {{tvdbid}}
		};

		$('#search_result').DataTable( {
		    destroy: true,
		    language: {
				loadingRecords: "Searching for subtitles..."
		    },
		    paging: true,
    		searching: false,
    		ordering: false,
    		processing: false,
        	serverSide: false,
        	lengthMenu: [ [ 5, 10, 25, 50, 100 , -1 ] , [ 5, 10, 25, 50, 100, "All" ] ],
    		ajax: {
				url: '{{base_url}}manual_search',
				type: 'POST',
                data: values
			},
			columns: [
				{ data: 'score' },
				{ data: 'hearing_impaired' },
				{ data: 'provider' }
			]
		} );

		$('.search_dialog')
			.modal({
				centered: false
			})
			.modal('show')
		;
	})
</script>
