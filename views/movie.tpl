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
				background-image: url("{{base_url}}image_proxy_movies{{details[3]}}");
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
				text-color: black;
				overflow-x:auto;
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
	</head>
	<body>
		%import ast
		%from get_languages import *
        %from config import settings
        %from helper import path_replace_movie
		%single_language = settings.general.getboolean('single_language')
		<div style="display: none;"><img src="{{base_url}}image_proxy_movies{{details[3]}}"></div>
		<div id='loader' class="ui page dimmer">
		   	<div id="loader_text" class="ui indeterminate text loader">Loading...</div>
		</div>
		% include('menu.tpl')
		
		<div style='padding-left: 2em; padding-right: 2em;' class='ui container'>
			<div id="divdetails" class="ui container">
				<div class="ui stackable grid">
					<div class="three wide column">
						<img class="left floated ui image" style="max-height:250px;" src="{{base_url}}image_proxy_movies{{details[2]}}">
					</div>

					<div class="thirteen wide column">
						<div class="ui stackable grid">
							<div class="ui row">
								<div class="twelve wide left aligned column">
									<h2>
					                    %if details[13] == 'True':
					                    <span data-tooltip="Movie monitored in Radarr"><i class="bookmark icon"></i></span>
					                    %else:
					                    <span data-tooltip="Movie unmonitored in Radarr"><i class="bookmark outline icon"></i></span>
					                    %end
										{{details[0]}}
					                </h2>
								</div>

								<div class="four wide right aligned column">
									<div class="ui right floated basic icon buttons">
										<button id="scan_disk" class="ui button" data-tooltip="Scan disk for subtitles" data-inverted=""><i class="ui inverted large compact refresh icon"></i></button>
										<button id="search_missing_subtitles_movie" class="ui button" data-tooltip="Download missing subtitles" data-inverted=""><i class="ui inverted huge compact search icon"></i></button>
										<%
										subs_languages = ast.literal_eval(str(details[7]))
										subs_languages_list = []
										if subs_languages is not None:
											for subs_language in subs_languages:
												subs_languages_list.append(subs_language)
											end
										end
										%>
										%if subs_languages is not None:
										<button class="manual_search ui button" data-tooltip="Manually search for subtitles" data-inverted="" data-moviePath="{{details[8]}}" data-scenename="{{details[12]}}" data-language="{{subs_languages_list}}" data-hi="{{details[4]}}" data-forced="{{details[15]}}" data-movie_title="{{details[0]}}" data-radarrId="{{details[10]}}"><i class="ui inverted large compact user icon"></i></button>
										<button class="manual_upload ui button" data-tooltip="Manually upload subtitles" data-inverted="" data-moviePath="{{details[8]}}" data-scenename="{{details[12]}}" data-language="{{subs_languages_list}}" data-hi="{{details[4]}}" data-movie_title="{{details[0]}}" data-radarrId="{{details[10]}}"><i class="ui inverted large compact cloud upload icon"></i></button>
										%end
										<button id="config" class="ui button" data-tooltip="Edit movie" data-inverted="" data-tmdbid="{{details[5]}}" data-title="{{details[0]}}" data-poster="{{details[2]}}" data-audio="{{details[6]}}" data-languages="{{!subs_languages_list}}" data-hearing-impaired="{{details[4]}}" data-forced="{{details[15]}}"><i class="ui inverted large compact configure icon"></i></button>
									</div>
								</div>
							</div>

							<div class="ui row">
								{{details[1]}}
							</div>

							<div class="ui row">
								<div class="ui tiny inverted label" style='background-color: #777777;'>{{details[6]}}</div>
								<div class="ui tiny inverted label" style='background-color: #35c5f4;'>{{details[8]}}</div>
								% if details[12] is not None:
								<div class="ui tiny inverted label" style='background-color: orange;'>{{details[12]}}</div>
								% end
							</div>

							<div class="ui row" style="padding-bottom: 0.5em;">
								%for language in subs_languages_list:
								<div class="ui tiny inverted label" style='background-color: #35c5f4;'>{{language}}</div>
								%end
							</div>

							<div class="ui row" style="padding-top: 0em;">
								<div class="ui tiny inverted label" style='background-color: #777777;'>Hearing-impaired: {{details[4]}}</div>
								<div class="ui tiny inverted label" style='background-color: #777777;'>Forced: {{details[15]}}</div>
							</div>
						</div>
					</div>
				</div>

				<div id="fondblanc" class="ui container">
					<table class="ui very basic single line selectable table">
						<thead>
							<tr>
								<th>Subtitles path</th>
								<th>Language</th>
								<th></th>
							</tr>
						</thead>
						<tbody>
							<%
							subtitles_files = ast.literal_eval(str(details[9]))
							subtitles_files.sort()
							if subtitles_files is not None:
								for subtitles_file in subtitles_files:
									if subtitles_file[0].endswith(':forced'):
										forced = True
									else:
										forced = False
									end
							%>
							<tr>
								<td>{{path_replace_movie(subtitles_file[1]) if subtitles_file[1] is not None else 'Video file subtitles track'}}</td>
								<td><div class="ui tiny inverted label" style='background-color: #777777;'>{{language_from_alpha2(subtitles_file[0].split(':')[0])}}{{' forced' if forced else ''}}</div></td>
								<td>
									%if subtitles_file[1] is not None:
									<a class="remove_subtitles ui inverted basic compact icon" data-tooltip="Delete subtitles file from disk" data-inverted="" data-position="top right" data-moviePath="{{details[8]}}" data-subtitlesPath="{{path_replace_movie(subtitles_file[1])}}" data-language="{{alpha3_from_alpha2(subtitles_file[0].split(':')[0])}}" data-radarrId={{details[10]}}>
										<i class="ui black delete icon"></i>
									</a>
									%end
								</td>
							</tr>
							<%
								end
								if len(subtitles_files) == 0:
							%>
							<tr><td colspan="3">No subtitles detected for this movie.</td></tr>
							<%
								end
							end
							%>
						</tbody>
					</table>
					<%
					if details[11] is not None:
						missing_subs_languages = ast.literal_eval(details[11])
					else:
						missing_subs_languages = []
					end
                	from get_subtitle import search_active
					if missing_subs_languages is not None:
					%>
					<table class="ui very basic single line selectable table">
						<thead>
							<tr>
								<th>Missing subtitles</th>
							</tr>
						</thead>
					</table>
					<%
						for missing_subs_language in missing_subs_languages:
							if len(missing_subs_language) > 2:
								forced = missing_subs_language[2]
								forced_bool = True
							else:
								forced = False
								forced_bool = False
							end

						    if details[14] is not None and settings.general.getboolean('adaptive_searching') and missing_subs_language in details[14]:
                                for lang in ast.literal_eval(details[14]):
                                    if missing_subs_language in lang:
                                        if search_active(lang[1]):
					%>
							<a class="get_subtitle ui small blue label" data-moviePath="{{details[8]}}" data-scenename="{{details[12]}}" data-language="{{alpha3_from_alpha2(str(missing_subs_language.split(':')[0]))}}" data-hi="{{details[4]}}" data-forced="{{forced_bool}}" data-radarrId={{details[10]}}>
								{{language_from_alpha2(str(missing_subs_language.split(':')[0]))}}{{' forced' if forced else ''}}
								<i style="margin-left:3px; margin-right:0" class="search icon"></i>
							</a>
                                        %else:
                            <a data-tooltip="Automatic searching delayed (adaptive search)" data-position="top left" data-inverted="" class="get_subtitle ui small red label" data-moviePath="{{details[8]}}" data-scenename="{{details[12]}}" data-language="{{alpha3_from_alpha2(str(missing_subs_language.split(':')[0]))}}" data-hi="{{details[4]}}" data-forced="{{forced_bool}}" data-radarrId={{details[10]}}>
								{{language_from_alpha2(str(missing_subs_language.split(':')[0]))}}{{' forced' if forced else ''}}
								<i style="margin-left:3px; margin-right:0" class="search icon"></i>
							</a>
					<%
                                        end
                                    end
                                end
                            else:
                    %>
                            <a class="get_subtitle ui small blue label" data-moviePath="{{details[8]}}" data-scenename="{{details[12]}}" data-language="{{alpha3_from_alpha2(str(missing_subs_language.split(':')[0]))}}" data-hi="{{details[4]}}" data-forced="{{forced_bool}}" data-radarrId={{details[10]}}>
								{{language_from_alpha2(str(missing_subs_language.split(':')[0]))}}{{' forced' if forced else ''}}
								<i style="margin-left:3px; margin-right:0" class="search icon"></i>
							</a>
                    <%
                            end
						end
					end
					%>
				</div>
			</div>
		</div>

		<div class="config_dialog ui small modal">
			<i class="close icon"></i>
			<div class="header">
				<div id="movie_title"></div>
			</div>
			<div class="content">
				<form name="movie_form" id="movie_form" action="" method="post" class="ui form">
					<div class="ui grid">
						<div class="four wide column">
							<img id="movie_poster" class="ui image" src="">
						</div>
						<div class="twelve wide column">
							<div class="ui grid">
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Audio language</label>
									</div>
									<div class="nine wide column">
										<div id="movie_audio_language"></div>
									</div>
								</div>
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Subtitles languages</label>
									</div>
									<div class="nine wide column">
										<select name="languages" id="movie_languages" {{!'multiple="" ' if single_language is False else ''}} class="ui fluid selection dropdown">
											<option value="">Languages</option>
											%if single_language:
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
										<div id="movie_hearing-impaired_div" class="ui toggle checkbox">
											<input name="hearing_impaired" id="movie_hearing-impaired" type="checkbox">
											<label></label>
										</div>
									</div>
								</div>
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Forced</label>
									</div>
									<div class="nine wide column">
										<select name="forced" id="movie_forced" class="ui fluid selection dropdown">
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
				<button type="submit" name="save" value="save" form="movie_form" class="ui blue approve button">Save</button>
			</div>
		</div>

		<div class="search_dialog ui modal">
			<i class="close icon"></i>
			<div class="header">
				<span id="movie_title_span"></span>
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
				<span id="movie_title_upload_span"></span>
			</div>
			<div class="scrolling content">
				<form class="ui form" name="upload_form" id="upload_form" action="{{base_url}}manual_upload_subtitle_movie" method="post" enctype="multipart/form-data">
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
					<input type="hidden" id="upload_moviePath" name="moviePath" value="" />
					<input type="hidden" id="upload_sceneName" name="sceneName" value="" />
					<input type="hidden" id="upload_radarrId" name="radarrId" value="" />
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
		window.location = '{{base_url}}scan_disk_movie/{{no}}';
	});

	$('#search_missing_subtitles_movie').on('click', function(){
		$(this).addClass('disabled');
		$(this).find('i:first').addClass('loading');
	    $.ajax({
            url: '{{base_url}}search_missing_subtitles_movie/{{no}}'
        })
	});

	$('.remove_subtitles').on('click', function(){
		const values = {
			moviePath: $(this).attr("data-moviePath"),
			language: $(this).attr("data-language"),
			subtitlesPath: $(this).attr("data-subtitlesPath"),
			radarrId: $(this).attr("data-radarrId"),
			tmdbid: {{tmdbid}}
		};

		$('#loader_text').text("Deleting subtitle from disk...");

		$.ajax({
			url: "{{base_url}}remove_subtitles_movie",
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
			moviePath: $(this).attr("data-moviePath"),
			sceneName: $(this).attr("data-sceneName"),
			language: $(this).attr("data-language"),
			hi: $(this).attr("data-hi"),
			forced: $(this).attr("data-forced"),
			radarrId: $(this).attr("data-radarrId"),
			tmdbid: {{tmdbid}},
			title: "{{!details[0].replace("'", "\\'")}}"
		};

		$('#loader_text').text("Downloading subtitle to disk...");

		$.ajax({
			url: "{{base_url}}get_subtitle_movie",
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

	$('a, .menu .item, button:not(#config, .cancel, .manual_search, .manual_upload, #search_missing_subtitles_movie)').on('click', function(){
		$('#loader').addClass('active');
	});

	$('#config').on('click', function(){
		$('#movie_form').attr('action', '{{base_url}}edit_movie/{{no}}');

		$("#movie_title").html($(this).data("title"));
		$("#movie_poster").attr("src", "{{base_url}}image_proxy_movies" + $(this).data("poster"));

		$("#movie_audio_language").html($(this).data("audio"));

		$('#movie_languages').dropdown('clear');
		const languages_array = eval($(this).data("languages"));
		$('#movie_languages').dropdown('set selected',languages_array);

		$('#movie_forced').dropdown('clear');
		$('#movie_forced').dropdown('set selected',$(this).data("forced"));

		if ($(this).data("hearing-impaired") === "True") {
			$("#movie_hearing-impaired_div").checkbox('check');
		} else {
			$("#movie_hearing-impaired_div").checkbox('uncheck');
		}

		$('.config_dialog')
			.modal({
				centered: false,
				autofocus: false
			})
			.modal('show');
	});

	$('.manual_search').on('click', function(){
		$("#movie_title_span").html($(this).data("movie_title"));

		moviePath = $(this).attr("data-moviePath");
		sceneName = $(this).attr("data-sceneName");
		language = $(this).attr("data-language");
		hi = $(this).attr("data-hi");
		forced = $(this).attr("data-forced");
		radarrId = $(this).attr("data-radarrId");
		var languages = Array.from({{!subs_languages_list}});
		var is_pb = languages.includes('pb');
		var is_pt = languages.includes('pt');

		const values = {
			moviePath: moviePath,
			sceneName: sceneName,
			language: language,
			hi: hi,
			forced: forced,
			radarrId: radarrId,
			title: "{{!details[0].replace("'", "\'")}}"
		};

		$('#search_result').DataTable( {
		    destroy: true,
		    language: {
				loadingRecords: '<br><div class="ui active inverted dimmer" style="width: 95%;"><div class="ui centered inline loader"></div></div><br>',
				zeroRecords: 'No subtitles found for this movie'
		    },
		    paging: true,
			lengthChange: false,
			pageLength: 5,
    		searching: false,
    		ordering: false,
    		processing: false,
        	serverSide: false,
        	ajax: {
				url: '{{base_url}}manual_search_movie',
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
					} else if ( data.language === "pt:forced" && is_pb === true && is_pt === false) {
		    			return 'pb:forced'
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
        			return '<a href="#" class="ui tiny label" onclick="manual_get(this, moviePath, sceneName, hi, radarrId)" data-subtitle="'+data.subtitle+'" data-provider="'+data.provider+'" data-language="'+data.language+'"><i class="ui download icon" style="margin-right:0px" ></i></a>';
    				}
				}
			]
		} );

		$('.search_dialog')
			.modal({
				centered: false,
				autofocus: false
			})
			.modal('show')
		;
	});

	$('.manual_upload').on('click', function() {
		$("#movie_title_upload_span").html($(this).data("movie_title"));

		moviePath = $(this).attr("data-moviePath");
		sceneName = $(this).attr("data-sceneName");
		language = $(this).attr("data-language");
		radarrId = $(this).attr("data-radarrId");
		var title = "{{!details[0].replace("'", "\'")}}";

		$('#language').dropdown();

		$('#upload_moviePath').val(moviePath);
		$('#upload_sceneName').val(sceneName);
		$('#upload_radarrId').val(radarrId);
		$('#upload_title').val(title);

		$('.upload_dialog')
			.modal({
				centered: false,
				autofocus: false
			})
			.modal('show')
		;
	});

	function manual_get(button, episodePath, sceneName, hi){
		const values = {
				subtitle: $(button).attr("data-subtitle"),
				provider: $(button).attr("data-provider"),
				moviePath: moviePath,
				sceneName: sceneName,
				language: $(button).attr("data-language"),
				hi: hi,
				radarrId: radarrId,
				title: "{{!details[0].replace("'", "\\'")}}"
		};

		$('#loader_text').text("Downloading subtitle to disk...");
		$('#loader').addClass('active');

		$('.search_dialog').modal('hide');

		$.ajax({
			url: "{{base_url}}manual_get_subtitle_movie",
			type: "POST",
			dataType: "json",
			data: values
		});
		$(document).ajaxStop(function(){
			window.location.reload();
		});
	}
</script>