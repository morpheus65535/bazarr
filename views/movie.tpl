<html>
	<head>
		<!DOCTYPE html>
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
	</head>
	<body>
		%import ast
		%import pycountry
		%from get_general_settings import *
		%single_language = get_general_settings()[7]
		<div style="display: none;"><img src="{{base_url}}image_proxy{{details[3]}}"></div>
		<div id='loader' class="ui page dimmer">
		   	<div class="ui indeterminate text loader">Loading...</div>
		</div>
		% include('menu.tpl')
		
		<div style='padding-left: 2em; padding-right: 2em;' class='ui container'>	
			<div id="divdetails" class="ui container">
				<img class="left floated ui image" src="{{base_url}}image_proxy_movies{{details[2]}}">
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
					<button id="config" class="ui button" data-tooltip="Edit movie" data-inverted="" data-tmdbid="{{details[5]}}" data-title="{{details[0]}}" data-poster="{{details[2]}}" data-audio="{{details[6]}}" data-languages="{{!subs_languages_list}}" data-hearing-impaired="{{details[4]}}"><i class="ui inverted large compact configure icon"></i></button>
				</div>
				<h2>{{details[0]}}</h2>
				<p>{{details[1]}}</p>
				<p style='margin-top: 3em;'>
					<div class="ui tiny inverted label" style='background-color: #777777;'>{{details[6]}}</div>
					<div class="ui tiny inverted label" style='background-color: #35c5f4;'>{{details[8]}}</div>
				</p>
				<p style='margin-top: 2em;'>
					%for language in subs_languages_list:
					<div class="ui tiny inverted label" style='background-color: #35c5f4;'>{{language}}</div>
					%end
				</p>
				<div style='clear:both;'></div>
			</div>
		</div>

		<div class="ui small modal">
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
										<select name="languages" id="movie_languages" {{!'multiple="" ' if single_language == 'False' else ''}} class="ui fluid selection dropdown">
											<option value="">Languages</option>
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
		            sonarrmovieId: $(this).attr("data-sonarrmovieId"),
		            sonarrEpisodeId: $(this).attr("data-sonarrEpisodeId"),
		            tmdbid: {{tmdbid}}
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
		            hi: $(this).attr("data-hi"),
		            sonarrmovieId: $(this).attr("data-sonarrmovieId"),
		            sonarrEpisodeId: $(this).attr("data-sonarrEpisodeId"),
		            tmdbid: {{tmdbid}}
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

	$('a, i').click(function(){
		$('#loader').addClass('active');
	})

	$('.modal')
		.modal({
			autofocus: false
		})
	;

	$('#config').click(function(){
		$('#movie_form').attr('action', '{{base_url}}edit_movie/{{no}}');

		$("#movie_title").html($(this).data("title"));
		$("#movie_poster").attr("src", "{{base_url}}image_proxy_movies" + $(this).data("poster"));

		$("#movie_audio_language").html($(this).data("audio"));

		$('#movie_languages').dropdown('clear');
		var languages_array = eval($(this).data("languages"));
		$('#movie_languages').dropdown('set selected',languages_array);

		if ($(this).data("hearing-impaired") == "True") {
			$("#movie_hearing-impaired_div").checkbox('check');
		} else {
			$("#movie_hearing-impaired_div").checkbox('uncheck');
		}

		$('.small.modal').modal('show');
	})
</script>