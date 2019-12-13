<!DOCTYPE html>
<html lang="en">
	<head>
		<script src="{{base_url}}static/jquery/jquery-latest.min.js"></script>
		<script src="{{base_url}}static/semantic/semantic.min.js"></script>
		<link rel="stylesheet" href="{{base_url}}static/semantic/semantic.min.css">

		<link rel="apple-touch-icon" sizes="120x120" href="{{base_url}}static/apple-touch-icon.png">
		<link rel="icon" type="image/png" sizes="32x32" href="{{base_url}}static/favicon-32x32.png">
		<link rel="icon" type="image/png" sizes="16x16" href="{{base_url}}static/favicon-16x16.png">
		<link rel="manifest" href="{{base_url}}static/manifest.json">
		<link rel="mask-icon" href="{{base_url}}static/safari-pinned-tab.svg" color="#5bbad5">
		<link rel="shortcut icon" href="{{base_url}}static/favicon.ico">
		<meta name="msapplication-config" content="{{base_url}}static/browserconfig.xml">
		<meta name="theme-color" content="#ffffff">

		<title>Movies - Bazarr</title>

		<style>
			body {
				background-color: #272727;
			}
			#fondblanc {
				background-color: #ffffff;
				border-radius: 0;
				box-shadow: 0 0 5px 5px #ffffff;
				margin-top: 32px;
				margin-bottom: 3em;
				padding: 2em 3em 2em 3em;
				overflow-x:auto;
			}
			#tablemovies {
				padding-top: 1em;
			}
			#divdetails {
				min-height: 250px;
			}
			.fast.backward, .backward, .forward, .fast.forward {
				cursor: pointer;
			}
			.fast.backward, .backward, .forward, .fast.forward { pointer-events: auto; }
			.fast.backward.disabled, .backward.disabled, .forward.disabled, .fast.forward.disabled { pointer-events: none; }
		</style>
	</head>
	<body>
		<div id='loader' class="ui page dimmer">
			<div id="loader_text" class="ui indeterminate text loader">Loading...</div>
		</div>
		% include('menu.tpl')

		<div id="fondblanc" class="ui container">
			<div class="ui basic buttons">
				<button id="movieseditor" class="ui button"><i class="configure icon"></i>Movies Editor</button>
			</div>
			<table id="tablemovies" class="ui very basic selectable stackable table">
				<thead>
					<tr>
						<th></th>
						<th>Name</th>
						<th>Path</th>
						<th>Audio<br>Language</th>
						<th>Subtitles<br>Languages</th>
						<th>Hearing-<br>Impaired</th>
						<th>Forced</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
				%import ast
				%import os
				%for row in rows:
					<tr class="selectable">
						<td>
							%if row['monitored'] == "True":
							<span data-tooltip="Movie monitored in Radarr" data-inverted="" data-position="top left"><i class="bookmark icon"></i></span>
							%else:
							<span data-tooltip="Movie unmonitored in Radarr" data-inverted="" data-position="top left"><i class="bookmark outline icon"></i></span>
							%end
						</td>
						<td>
							% if row['sceneName'] is not None:
							<span data-tooltip="Scenename is: {{row['sceneName']}}" data-inverted='' data-position="top left"><i class="info circle icon"></i></span>
							% end
							<a href="{{base_url}}movie/{{row['radarrId']}}">{{row['title']}}</a>
						</td>
						<td>
							%if os.path.isfile(row['path']):
							<span data-tooltip="This path seems to be valid." data-inverted="" data-position="top left"><i class="checkmark icon"></i></span>
							%else:
							<span data-tooltip="This path doesn't seem to be valid." data-inverted="" data-position="top left"><i class="warning sign icon"></i></span>
							%end
							{{row['path']}}
						</td>
						<td>{{row['audio_language']}}</td>
						<td>
							%subs_languages = ast.literal_eval(str(row['languages']))
							%if subs_languages is not None:
								%for subs_language in subs_languages:
									<div class="ui tiny label">{{subs_language}}</div>
								%end
							%end
						</td>
						<td>{{!"" if row['hearing_impaired'] is None else row['hearing_impaired']}}</td>
						<td>{{row['forced']}}</td>
						<td {{!"style='background-color: #e8e8e8;'" if row['hearing_impaired'] is None else ""}}>
							<%
							subs_languages_list = []
							if subs_languages is not None:
								for subs_language in subs_languages:
									subs_languages_list.append(subs_language)
								end
							end
							%>
							<div class="config ui inverted basic compact icon" data-tooltip="Edit Movie" data-inverted="" data-position="top right" data-no="{{row['radarrId']}}" data-title="{{row['title']}}" data-poster="{{row['poster']}}" data-languages="{{!subs_languages_list}}" data-forced="{{row['forced']}}" data-hearing-impaired="{{row['hearing_impaired']}}" data-audio="{{row['audio_language']}}">
								<i class="ui black configure icon"></i>
							</div>
						</td>
					</tr>
				%end
				</tbody>
			</table>
			%try: page_size
			%except NameError: page_size = "25"
			%end
			%if page_size != -1:
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
					<div class="right floated right aligned column">Total Records: {{missing_count}}</div>
				</div>
			</div>
			%end
		</div>

		<div class="ui small modal">
			<i class="close icon"></i>
			<div class="header">
				<div id="movies_title"></div>
			</div>
			<div class="content">
				<form name="movies_form" id="movies_form" action="" method="post" class="ui form">
					<div id="divdetails" class="ui grid">
						<div class="four wide column">
							<img id="movies_poster" class="ui image" src="">
						</div>
						<div class="twelve wide column">
							<div class="ui grid">
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Audio Language</label>
									</div>
									<div class="nine wide column">
										<div id="movies_audio_language"></div>
									</div>
								</div>
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Subtitle Languages</label>
									</div>
									<div class="nine wide column">
										<select name="languages" id="movies_languages" {{!'multiple="" ' if single_language is False else ''}}class="ui fluid selection dropdown">
											<option value="">Languages</option>
											%if single_language:
                                        	<option value="None">None</option>
                                        	%end
											%for language in languages:
											<option value="{{language['code2']}}">{{language['name']}}</option>
											%end
										</select>
									</div>
								</div>
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Hearing-Impaired</label>
									</div>
									<div class="nine wide column">
										<div id="movies_hearing-impaired_div" class="ui toggle checkbox">
											<input name="hearing_impaired" id="movies_hearing-impaired" type="checkbox">
											<label></label>
										</div>
									</div>
								</div>
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Forced</label>
									</div>
									<div class="nine wide column">
										<select name="forced" id="movies_forced" class="ui fluid selection dropdown">
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
				<button type="submit" name="save" value="save" form="movies_form" class="ui blue approve button">Save</button>
			</div>
		</div>

		% include('footer.tpl')
	</body>
</html>


<script>
	if (sessionStorage.scrolly) {
		$(window).scrollTop(sessionStorage.scrolly);
		sessionStorage.clear();
	}

	$('a, button:not(.cancel)').on('click', function(){
		$('#loader').addClass('active');
	});

	$('.fast.backward').on('click', function(){
		location.href="?page=1";
	});
	$('.backward:not(.fast)').on('click', function(){
		location.href="?page={{int(page)-1}}";
	});
	$('.forward:not(.fast)').on('click', function(){
		location.href="?page={{int(page)+1}}";
	});
	$('.fast.forward').on('click', function(){
		location.href="?page={{int(max_page)}}";
	});

	$('#movieseditor').on('click', function(){
		window.location = '{{base_url}}movieseditor';
	});

	$('.modal')
		.modal({
			autofocus: false
		})
	;

	$('.config').on('click', function(){
		sessionStorage.scrolly=$(window).scrollTop();

		$('#movies_form').attr('action', '{{base_url}}edit_movie/' + $(this).data("no"));

		$("#movies_title").html($(this).data("title"));
		$("#movies_poster").attr("src", "{{base_url}}image_proxy_movies" + $(this).data("poster"));

		$("#movies_audio_language").html($(this).data("audio"));

		$('#movies_languages').dropdown('clear');
		var languages_array = eval($(this).data("languages"));
		$('#movies_languages').dropdown('set selected',languages_array);

		$('#movies_forced').dropdown('clear');
		$('#movies_forced').dropdown('set selected',$(this).data("forced"));

		if ($(this).data("hearing-impaired") === "True") {
			$("#movies_hearing-impaired_div").checkbox('check');
		} else {
			$("#movies_hearing-impaired_div").checkbox('uncheck');
		}

		$('.small.modal').modal('show');
	});

	$('#movies_languages').dropdown();
</script>
