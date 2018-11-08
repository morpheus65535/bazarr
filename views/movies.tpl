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

		<title>Movies - Bazarr</title>

		<style>
			body {
				background-color: #272727;
			}
			#fondblanc {
				background-color: #ffffff;
				border-radius: 0px;
				box-shadow: 0px 0px 5px 5px #ffffff;
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
			<table id="tablemovies" class="ui very basic selectable table">
				<thead>
					<tr>
						<th></th>
						<th class="sorted ascending">Name</th>
						<th>Path</th>
						<th>Audio<br>language</th>
						<th>Subtitles<br>languages</th>
						<th>Hearing-<br>impaired</th>
						<th class="no-sort"></th>
					</tr>
				</thead>
				<tbody>
				%import ast
				%import os
				%for row in rows:
					<tr class="selectable">
						<td>
							%if row[8] == "True":
							<span data-tooltip="Movie monitored in Radarr"><i class="bookmark icon"></i></span>
							%else:
							<span data-tooltip="Movie unmonitored in Radarr"><i class="bookmark outline icon"></i></span>
							%end
						</td>
						<td><a href="{{base_url}}movie/{{row[5]}}">{{row[1]}}</a></td>
						<td>
							%if os.path.isfile(row[2].encode("UTF-8")):
							<span data-tooltip="This path seems to be valid." data-inverted=""><i class="checkmark icon"></i></span>
							%else:
							<span data-tooltip="This path doesn't seems to be valid." data-inverted=""><i class="warning sign icon"></i></span>
							%end
							{{row[2]}}
						</td>
						<td>{{row[7]}}</td>
						<td>
							%subs_languages = ast.literal_eval(str(row[3]))
							%if subs_languages is not None:
								%for subs_language in subs_languages:
									<div class="ui tiny label">{{subs_language}}</div>
								%end
							%end
						</td>
						<td>{{!"" if row[4] == None else row[4]}}</td>
						<td {{!"style='background-color: #e8e8e8;'" if row[4] == None else ""}}>
							<%
							subs_languages_list = []
							if subs_languages is not None:
								for subs_language in subs_languages:
									subs_languages_list.append(subs_language)
								end
							end
							%>
							<div class="config ui inverted basic compact icon" data-tooltip="Edit movies" data-inverted="" data-no="{{row[5]}}" data-title="{{row[1]}}" data-poster="{{row[6]}}" data-languages="{{!subs_languages_list}}" data-hearing-impaired="{{row[4]}}" data-audio="{{row[7]}}">
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
					<div class="right floated right aligned column">Total records: {{missing_count}}</div>
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
										<label>Audio language</label>
									</div>
									<div class="nine wide column">
										<div id="movies_audio_language"></div>
									</div>
								</div>
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Subtitles languages</label>
									</div>
									<div class="nine wide column">
										<select name="languages" id="movies_languages" {{!'multiple="" ' if single_language is False else ''}}class="ui fluid selection dropdown">
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
										<div id="movies_hearing-impaired_div" class="ui toggle checkbox">
											<input name="hearing_impaired" id="movies_hearing-impaired" type="checkbox">
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

	$('table').tablesort();

	$('a, button:not(.cancel)').click(function(){
		$('#loader').addClass('active');
	})

	$('.fast.backward').click(function(){
		location.href="?page=1";
	})
	$('.backward:not(.fast)').click(function(){
		location.href="?page={{int(page)-1}}";
	})
	$('.forward:not(.fast)').click(function(){
		location.href="?page={{int(page)+1}}";
	})
	$('.fast.forward').click(function(){
		location.href="?page={{int(max_page)}}";
	})

	$('#movieseditor').click(function(){
		window.location = '{{base_url}}movieseditor';
	})

	$('.modal')
		.modal({
			autofocus: false
		})
	;

	$('.config').click(function(){
		sessionStorage.scrolly=$(window).scrollTop();

		$('#movies_form').attr('action', '{{base_url}}edit_movie/' + $(this).data("no"));

		$("#movies_title").html($(this).data("title"));
		$("#movies_poster").attr("src", "{{base_url}}image_proxy_movies" + $(this).data("poster"));

		$("#movies_audio_language").html($(this).data("audio"));

		$('#movies_languages').dropdown('clear');
		var languages_array = eval($(this).data("languages"));
		$('#movies_languages').dropdown('set selected',languages_array);

		if ($(this).data("hearing-impaired") == "True") {
			$("#movies_hearing-impaired_div").checkbox('check');
		} else {
			$("#movies_hearing-impaired_div").checkbox('uncheck');
		}

		$('.small.modal').modal('show');
	})

	$('#movies_languages').dropdown();
</script>
