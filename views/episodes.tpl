<!DOCTYPE html>
<html lang="en">
	<head>
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
				background-color: rgba(0, 0, 0, 0.9);
				color: #ffffff;
				margin-top: 6em;
				margin-bottom: 3em;
				padding: 2em;
				border-radius: 1px;
				box-shadow: 0 0 5px 5px #000000;
				min-height: calc(250px + 4em);
			}
			#fondblanc {
				background-color: #ffffff;
				opacity: 0.9;
				border-radius: 1px;
				box-shadow: 0 0 3px 3px #ffffff;
				margin-top: 32px;
				margin-bottom: 3em;
				padding-top: 2em;
				padding-left: 2em;
				padding-right: 2em;
				padding-bottom: 1em;
				overflow-x: auto;
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

			.criteria_matched {
				background-color: #e6ffe6 !important;
				line-height: 0 !important;
			}

			.criteria_not_matched {
				background-color: #ffcccc !important;
				line-height: 0 !important;
			}
		</style>

		<script>
           	$(function(){
            	$('.ui.accordion').accordion();
            	const first_season_acc_title = document.getElementsByClassName("title")[0];
            	first_season_acc_title.className += " active";
            	const first_season_acc_content = document.getElementsByClassName("content")[0];
            	first_season_acc_content.className += " active";
            });
		</script>
	</head>
	<body>
		%import ast
		%from get_languages import *
        %from config import settings
        %from helper import path_replace
		%single_language = settings.general.getboolean('single_language')
		<div style="display: none;"><img src="{{base_url}}image_proxy{{details[3]}}"></div>
		<div id='loader' class="ui page dimmer">
		   	<div id="loader_text" class="ui indeterminate text loader">Loading...</div>
		</div>
		% include('menu.tpl')
		
		<div style='padding-left: 2em; padding-right: 2em;' class='ui container'>	
			<div id="divdetails" class="ui container">
				<div class="ui stackable grid">
					<div class="three wide column">
						<img class="ui image" style="max-height:250px;" src="{{base_url}}image_proxy{{details[2]}}">
					</div>

					<div class="thirteen wide column">
						<div class="ui stackable grid">
							<div class="ui row">
								<div class="twelve wide left aligned column">
									<h2>{{details[0]}}</h2>
								</div>

								<div class="four wide right aligned column">
									<div class="ui basic icon buttons">
										<button id="scan_disk" class="ui button" data-tooltip="Scan disk for subtitles"><i class="ui inverted large compact refresh icon"></i></button>
										<button id="search_missing_subtitles" class="ui button" data-tooltip="Download missing subtitles"><i class="ui inverted huge compact search icon"></i></button>
										<%
										subs_languages = ast.literal_eval(str(details[7]))
										subs_languages_list = []
										if subs_languages is not None:
											for subs_language in subs_languages:
												subs_languages_list.append(subs_language)
											end
										end
										%>
										<button id="config" class="ui button" data-tooltip="Edit series" data-tvdbid="{{details[5]}}" data-title="{{details[0]}}" data-poster="{{details[2]}}" data-audio="{{details[6]}}" data-languages="{{!subs_languages_list}}" data-hearing-impaired="{{details[4]}}" data-forced="{{details[9]}}"><i class="ui inverted large compact configure icon"></i></button>
									</div>
								</div>
							</div>

							<div class="ui row">
								<p>{{details[1]}}</p>
							</div>

							<div class="ui row">
								<div class="ui tiny inverted label" style='background-color: #777777;'>{{details[6]}}</div>
								<div class="ui tiny inverted label" style='background-color: #35c5f4;'>{{details[8]}}</div>
								<div class="ui tiny inverted label" style='background-color: #35c5f4;'>{{number}} files</div>
							</div>

							<div class="ui row" style="padding-bottom: 0.5em;">
								%for language in subs_languages_list:
								<div class="ui tiny inverted label" style='background-color: #35c5f4;'>{{language}}</div>
								%end
							</div>

							<div class="ui row" style="padding-top: 0em;">
								<div class="ui tiny inverted label" style='background-color: #777777;'>Hearing-impaired: {{details[4]}}</div>
								<div class="ui tiny inverted label" style='background-color: #777777;'>Forced: {{details[9]}}</div>
							</div>
						</div>
					</div>
				</div>
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
										<th class="collapsing">Manual<br>upload</th>
									</tr>
								</thead>
								<tbody>
								%for episode in season:
									<tr>
										<td class="collapsing">
                                            %if episode[9] == 'True':
                                            <span data-tooltip="Episode monitored in Sonarr" data-inverted='' data-position="top left"><i class="bookmark icon"></i></span>
                                            %else:
                                            <span data-tooltip="Episode unmonitored in Sonarr" data-inverted='' data-position="top left"><i class="bookmark outline icon"></i></span>
                                            %end
                                        </td>
										<td>{{episode[3]}}</td>
										<td>
											% if episode[8] is not None:
											<span data-tooltip="Scenename is: {{episode[8]}}" data-inverted='' data-position="top left"><i class="info circle icon"></i></span>
                                       	% end
											<span data-tooltip="Path is: {{episode[1]}}" data-inverted='' data-position="top left">{{episode[0]}}</span>
										</td>
										<td>
										%if episode[4] is not None:
										%	actual_languages = ast.literal_eval(episode[4])
                                        %   actual_languages.sort()
										%else:
										%	actual_languages = '[]'
										%end
										%try:
											%for language in actual_languages:
												%if language[0].endswith(':forced'):
												%	forced = True
												%else:
												%	forced = False
												%end
												%if language[1] is not None:
												<a data-episodePath="{{episode[1]}}" data-subtitlesPath="{{path_replace(language[1])}}" data-language="{{alpha3_from_alpha2(str(language[0]))}}" data-sonarrSeriesId={{episode[5]}} data-sonarrEpisodeId={{episode[7]}} class="remove_subtitles ui tiny label">
                                                    {{!'<span class="ui" data-tooltip="Forced" data-inverted=""><i class="exclamation icon"></i></span>' if forced else ''}}{{language[0].split(':')[0]}}
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
                                        <%
                                            if episode[6] is not None:
                                                missing_languages = ast.literal_eval(episode[6])
                                                missing_languages.sort()
											end
											if missing_languages is not None:
                                                from get_subtitle import search_active
                                                for language in missing_languages:
													if episode[10] is not None and settings.general.getboolean('adaptive_searching') and language in episode[10]:
                                                        for lang in ast.literal_eval(episode[10]):
                                                            if language in lang:
																if search_active(lang[1]):
                                        %>
                                                                    <a data-episodePath="{{episode[1]}}" data-scenename="{{episode[8]}}" data-language="{{alpha3_from_alpha2(str(language.split(':')[0]))}}" data-hi="{{details[4]}}" data-forced="{{"True" if len(language.split(':')) > 1 else "False"}}" data-sonarrSeriesId="{{episode[5]}}" data-sonarrEpisodeId="{{episode[7]}}" class="get_subtitle ui tiny label">
													                {{language}}
                                                                    <i style="margin-left:3px; margin-right:0" class="search icon"></i>
                                                                    </a>
                                                                %else:
                                                                    <a data-tooltip="Automatic searching delayed (adaptive search)" data-position="top right" data-inverted="" data-episodePath="{{episode[1]}}" data-scenename="{{episode[8]}}" data-language="{{alpha3_from_alpha2(str(language.split(':')[0]))}}" data-hi="{{details[4]}}" data-forced="{{"True" if len(language.split(':')) > 1 else "False"}}" data-sonarrSeriesId="{{episode[5]}}" data-sonarrEpisodeId="{{episode[7]}}" class="get_subtitle ui tiny label">
													                {{language}}
                                                                    <i style="margin-left:3px; margin-right:0" class="search red icon"></i>
                                                                    </a>
                                                                %end
                                                            %end
                                                        %end
                                                    %else:
                                                        <a data-episodePath="{{episode[1]}}" data-scenename="{{episode[8]}}" data-language="{{alpha3_from_alpha2(str(language.split(':')[0]))}}" data-hi="{{details[4]}}" data-forced="{{"True" if len(language.split(':')) > 1 else "False"}}" data-sonarrSeriesId="{{episode[5]}}" data-sonarrEpisodeId="{{episode[7]}}" class="get_subtitle ui tiny label">
                                                            {{language}}
                                                        <i style="margin-left:3px; margin-right:0" class="search icon"></i>
                                                        </a>
                                                    %end
                                                %end
											%end
                                        %except:
                                            %pass
										%end
										</td>
										<td>
											%if subs_languages is not None:
											<a data-episodePath="{{episode[1]}}" data-scenename="{{episode[8]}}" data-language="{{subs_languages_list}}" data-hi="{{details[4]}}" data-forced="{{details[9]}}" data-series_title="{{details[0]}}" data-season="{{episode[2]}}" data-episode="{{episode[3]}}" data-episode_title="{{episode[0]}}" data-sonarrSeriesId="{{episode[5]}}" data-sonarrEpisodeId="{{episode[7]}}" class="manual_search ui tiny label"><i class="ui user icon" style="margin-right:0px" ></i></a>
											%end
										</td>
										<td>
											%if subs_languages is not None:
											<a data-episodePath="{{episode[1]}}" data-scenename="{{episode[8]}}" data-language="{{subs_languages_list}}" data-hi="{{details[4]}}" data-series_title="{{details[0]}}" data-season="{{episode[2]}}" data-episode="{{episode[3]}}" data-episode_title="{{episode[0]}}" data-sonarrSeriesId="{{episode[5]}}" data-sonarrEpisodeId="{{episode[7]}}" class="manual_upload ui tiny label"><i class="ui cloud upload icon" style="margin-right:0px" ></i></a>
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
										<select name="languages" id="series_languages" {{!'multiple="" ' if single_language is False else ''}} class="ui fluid selection dropdown">
											<option value="">Languages</option>
										    %if single_language is True:
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
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Forced</label>
									</div>
									<div class="nine wide column">
										<select name="forced" id="series_forced" class="ui fluid selection dropdown">
											<option value="False">False</option>
											<option value="True">True</option>
											<option value="Both">Both</option>
										</select>
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
							<th style="text-align: left;">Score:</th>
							<th style="text-align: left;">Language:</th>
							<th style="text-align: left;">Hearing-impaired:</th>
							<th style="text-align: left;">Provider:</th>
							<th style="text-align: left;">Based on:</th>
							<th></th>
						</tr>
					</thead>
				</table>
			</div>
			<div class="actions">
				<button class="ui cancel button" >Cancel</button>
			</div>
		</div>

		<div class="upload_dialog ui small modal">
			<i class="close icon"></i>
			<div class="header">
				<span id="series_title_span_u"></span> - <span id="season_u"></span>x<span id="episode_u"></span> - <span id="episode_title_u"></span>
			</div>
			<div class="content">
				<form class="ui form" name="upload_form" id="upload_form" action="{{base_url}}manual_upload_subtitle" method="post" enctype="multipart/form-data">
					<div class="ui grid">
						<div class="middle aligned row">
							<div class="right aligned three wide column">
								<label>Language</label>
							</div>
							<div class="thirteen wide column">
								<select class="ui search dropdown" id="language" name="language">
									%for language in subs_languages_list:
									<option value="{{language}}">{{language_from_alpha2(language)}}</option>
									%end
								</select>
							</div>
						</div>
						<div class="middle aligned row">
							<div class="right aligned three wide column">
								<label>Forced</label>
							</div>
							<div class="thirteen wide column">
								<div class="ui toggle checkbox">
									<input name="forced" type="checkbox" value="1">
									<label></label>
								</div>
							</div>
						</div>
						<div class="middle aligned row">
							<div class="right aligned three wide column">
								<label>File</label>
							</div>
							<div class="thirteen wide column">
								<input type="file" name="upload">
							</div>
						</div>
					</div>
					<input type="hidden" id="upload_episodePath" name="episodePath" value="" />
					<input type="hidden" id="upload_sceneName" name="sceneName" value="" />
					<input type="hidden" id="upload_sonarrSeriesId" name="sonarrSeriesId" value="" />
					<input type="hidden" id="upload_sonarrEpisodeId" name="sonarrEpisodeId" value="" />
					<input type="hidden" id="upload_title" name="title" value="" />
				</form>
			</div>
			<div class="actions">
				<button class="ui cancel button" >Cancel</button>
				<button type="submit" name="save" value="save" form="upload_form" class="ui blue approve button">Save</button>
			</div>
		</div>

		% include('footer.tpl')
	</body>
</html>

<script>
	$('#scan_disk').on('click', function(){
		$('#loader_text').text("Scanning disk for existing subtitles...");
		window.location = '{{base_url}}scan_disk/{{no}}';
	});

	$('#search_missing_subtitles').on('click', function(){
		$(this).addClass('disabled');
		$(this).find('i:first').addClass('loading');
	    $.ajax({
            url: '{{base_url}}search_missing_subtitles/{{no}}'
        })
	});

	$('.remove_subtitles').on('click', function(){
		const values = {
			episodePath: $(this).attr("data-episodePath"),
			language: $(this).attr("data-language"),
			subtitlesPath: $(this).attr("data-subtitlesPath"),
			sonarrSeriesId: $(this).attr("data-sonarrSeriesId"),
			sonarrEpisodeId: $(this).attr("data-sonarrEpisodeId"),
			tvdbid: {{tvdbid}}
		};

		$('#loader_text').text("Deleting subtitle from disk...");

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
	});

	$('.get_subtitle').on('click', function(){
		const values = {
			episodePath: $(this).attr("data-episodePath"),
			sceneName: $(this).attr("data-sceneName"),
			language: $(this).attr("data-language"),
			hi: $(this).attr("data-hi"),
			forced: $(this).attr("data-forced"),
			sonarrSeriesId: $(this).attr('data-sonarrSeriesId'),
			sonarrEpisodeId: $(this).attr('data-sonarrEpisodeId'),
			title: "{{!details[0].replace("'", "\\'")}}"
		};

		$('#loader_text').text("Downloading subtitle to disk...");

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
	});

	$('a:not(.manual_search, .manual_upload), .menu .item, button:not(#config, .cancel, #search_missing_subtitles)').on('click', function(){
		$('#loader').addClass('active');
	});

	$('#config').on('click', function(){
		$('#series_form').attr('action', '{{base_url}}edit_series/{{no}}');

		$("#series_title").html($(this).data("title"));
		$("#series_poster").attr("src", "{{base_url}}image_proxy" + $(this).data("poster"));

		$("#series_audio_language").html($(this).data("audio"));

		$('#series_languages').dropdown('clear');
		const languages_array = eval($(this).data("languages"));
		$('#series_languages').dropdown('set selected',languages_array);

		$('#series_forced').dropdown('clear');
		$('#series_forced').dropdown('set selected',$(this).data("forced"));

		if ($(this).data("hearing-impaired") === "True") {
			$("#series_hearing-impaired_div").checkbox('check');
		} else {
			$("#series_hearing-impaired_div").checkbox('uncheck');
		}

		$('.config_dialog')
			.modal({
				centered: false,
				autofocus: false
			})
			.modal('show');
	});

	$('.manual_search').on('click', function(){
		$("#series_title_span").html($(this).data("series_title"));
		$("#season").html($(this).data("season"));
		$("#episode").html($(this).data("episode"));
		$("#episode_title").html($(this).data("episode_title"));

		episodePath = $(this).attr("data-episodePath");
		sceneName = $(this).attr("data-sceneName");
		language = $(this).attr("data-language");
        hi = $(this).attr("data-hi");
        forced = $(this).attr("data-forced");
		sonarrSeriesId = $(this).attr("data-sonarrSeriesId");
		sonarrEpisodeId = $(this).attr("data-sonarrEpisodeId");
		var languages = Array.from({{!subs_languages_list}});
		var is_pb = languages.includes('pb');
		var is_pt = languages.includes('pt');

		const values = {
			episodePath: episodePath,
			sceneName: sceneName,
			language: language,
			hi: hi,
			forced: forced,
			sonarrSeriesId: sonarrSeriesId,
			sonarrEpisodeId: sonarrEpisodeId,
			title: "{{!details[0].replace("'", "\'")}}"
		};

		$('#search_result').DataTable( {
		    destroy: true,
		    language: {
				loadingRecords: '<br><div class="ui active inverted dimmer" style="width: 95%;"><div class="ui centered inline loader"></div></div><br>',
				zeroRecords: 'No subtitles found for this episode'
		    },
		    paging: true,
    		lengthChange: false,
			pageLength: 5,
    		searching: false,
    		ordering: false,
    		processing: false,
        	serverSide: false,
        	ajax: {
				url: '{{base_url}}manual_search',
				type: 'POST',
                data: values
			},
			drawCallback: function(settings) {
                $('.inline.dropdown').dropdown();
			},
			columns: [
				{ data: 'score',
				render: function ( data, type, row ) {
        			return data +'%';
    				}
				},
				{ data: null,
				render: function ( data, type, row ) {
		    		if ( data.language === "pt" && is_pb === true && is_pt === false) {
		    			return 'pb'
					} else {
		    			return data.language
					}
					}
				},
				{ data: 'hearing_impaired' },
				{ data: null,
				render: function ( data, type, row ) {
        			return '<a href="'+data.url+'" target="_blank">'+data.provider+'</a>';
    				}
				},
				{ data: null,
				render: function ( data, type, row ) {
					const array_matches = data.matches;
					const array_dont_matches = data.dont_matches;
					let i;
					let text = '<div class="ui inline dropdown"><i class="green check icon"></i><div class="text">';
					text += array_matches.length;
					text += '</div><i class="dropdown icon"></i><div class="menu">';
					for (i = 0; i < array_matches.length; i++) {
						text += '<div class="criteria_matched disabled item">' + array_matches[i] + '</div>';
					}
					text += '</div></div>';
					text += '<div class="ui inline dropdown"><i class="red times icon"></i><div class="text">';
					text += array_dont_matches.length;
					text += '</div><i class="dropdown icon"></i><div class="menu">';
					for (i = 0; i < array_dont_matches.length; i++) {
						text += '<div class="criteria_not_matched disabled item">' + array_dont_matches[i] + '</div>';
					}
					text += '</div></div>';
        			return text;
    				}
				},
				{ data: null,
				render: function ( data, type, row ) {
        			return '<a href="#" class="ui tiny label" onclick="manual_get(this, episodePath, sceneName, hi, sonarrSeriesId, sonarrEpisodeId)" data-subtitle="'+data.subtitle+'" data-provider="'+data.provider+'" data-language="'+data.language+'"><i class="ui download icon" style="margin-right:0px" ></i></a>';
    				}
				}
			]
		} );

		$('.search_dialog')
			.modal({
				centered: false,
				autofocus: false
			})
			.modal('show');
	});

	$('.manual_upload').on('click', function(){
		$("#series_title_span_u").html($(this).data("series_title"));
		$("#season_u").html($(this).data("season"));
		$("#episode_u").html($(this).data("episode"));
		$("#episode_title_u").html($(this).data("episode_title"));

		episodePath = $(this).attr("data-episodePath");
		sceneName = $(this).attr("data-sceneName");
		language = $(this).attr("data-language");
        hi = $(this).attr("data-hi");
		sonarrSeriesId = $(this).attr("data-sonarrSeriesId");
		sonarrEpisodeId = $(this).attr("data-sonarrEpisodeId");
		var languages = Array.from({{!subs_languages_list}});
		var is_pb = languages.includes('pb');
		var is_pt = languages.includes('pt');
		var title = "{{!details[0].replace("'", "\'")}}";

		$('#language').dropdown();

		$('#upload_episodePath').val(episodePath);
		$('#upload_sceneName').val(sceneName);
		$('#upload_sonarrSeriesId').val(sonarrSeriesId);
		$('#upload_sonarrEpisodeId').val(sonarrEpisodeId);
		$('#upload_title').val(title);

		$('.upload_dialog')
			.modal({
				centered: false,
				autofocus: false
			})
			.modal('show');
	});

	function manual_get(button, episodePath, sceneName, hi, sonarrSeriesId, sonarrEpisodeId){
		const values = {
				subtitle: $(button).attr("data-subtitle"),
				provider: $(button).attr("data-provider"),
				episodePath: episodePath,
				sceneName: sceneName,
				language: $(button).attr("data-language"),
				hi: hi,
				sonarrSeriesId: sonarrSeriesId,
				sonarrEpisodeId: sonarrEpisodeId,
				title: "{{!details[0].replace("'", "\\'")}}"
		};

		$('#loader_text').text("Downloading subtitle to disk...");
		$('#loader').addClass('active');

		$('.search_dialog').modal('hide');

		$.ajax({
			url: "{{base_url}}manual_get_subtitle",
			type: "POST",
			dataType: "json",
			data: values
		});
		$(document).ajaxStop(function(){
			window.location.reload();
		});
	}
</script>
