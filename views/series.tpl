<html lang="en">
	<head>
		<!DOCTYPE html>
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

		<title>Series - Bazarr</title>

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
			#tableseries {
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
			.ui.progress:last-child {margin: 0 0 0 !important;}

			.ui.progress .bar>.progress {
                right: auto;
                left: .5em;
                color: rgba(0, 0, 0, 0.60);
            }
		</style>
	</head>
	<body>
		<div id='loader' class="ui page dimmer">
			<div id="loader_text" class="ui indeterminate text loader">Loading...</div>
		</div>
		% include('menu.tpl')

		<div id="fondblanc" class="ui container">
			<div class="ui basic buttons">
				<button id="serieseditor" class="ui button"><i class="configure icon"></i>Series Editor</button>
			</div>
			<table id="tableseries" class="ui very basic selectable table">
				<thead>
					<tr>
						<th>Name</th>
						<th>Path</th>
						<th>Audio language</th>
						<th>Subtitles languages</th>
						<th>Hearing-impaired</th>
						<th class="two wide">Subtitles</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
				%import ast
				%import os
				%for row in rows:
					<tr class="selectable">
						<td><a href="{{base_url}}episodes/{{row[5]}}">{{row[1]}}</a></td>
						<td>
							%if os.path.isdir(row[2]):
							<span data-tooltip="This path seems to be valid." data-inverted="" data-position="top left"><i class="checkmark icon"></i></span>
							%else:
							<span data-tooltip="This path doesn't seems to be valid." data-inverted="" data-position="top left"><i class="warning sign icon"></i></span>
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
						<td>{{!"" if row[4] is None else row[4]}}</td>
						<td>
							%total_subs = 0
							%missing_subs = 0
							%if not total_subtitles_list:
							%	pass
							%else:
							%	for total_subtitles in total_subtitles_list:
							%		if total_subtitles[0] == row[5]:
							%			total_subs = total_subtitles[1]
							%		end
							%	end
							%	for missing_subtitles in missing_subtitles_list:
							%		if missing_subtitles[0] == row[5]:
							%			missing_subs = missing_subtitles[1]
							%		end
							%	end
							%end
							<div class="ui progress" data-value="{{total_subs - missing_subs}}" data-total="{{total_subs}}">
								<div class="bar">
									<div class="progress"></div>
								</div>
							</div>
						</td>
						<td {{!"style='background-color: #e8e8e8;'" if row[4] == None else ""}}>
							<%
							subs_languages_list = []
							if subs_languages is not None:
								for subs_language in subs_languages:
									subs_languages_list.append(subs_language)
								end
							end
							%>
							<div class="config ui inverted basic compact icon" data-tooltip="Edit series" data-inverted="" data-position="top right" data-no="{{row[5]}}" data-title="{{row[1]}}" data-poster="{{row[6]}}" data-languages="{{!subs_languages_list}}" data-hearing-impaired="{{row[4]}}" data-audio="{{row[7]}}">
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
				<div id="series_title"></div>
			</div>
			<div class="content">
				<form name="series_form" id="series_form" action="" method="post" class="ui form">
					<div id="divdetails" class="ui grid">
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
										<select name="languages" id="series_languages" {{!'multiple="" ' if single_language is False else ''}}class="ui fluid selection dropdown">
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

	$('#serieseditor').on('click', function(){
		window.location = '{{base_url}}serieseditor';
	});

	$('.modal')
		.modal({
			autofocus: false
		});

	$('.config').on('click', function(){
		sessionStorage.scrolly=$(window).scrollTop();

		$('#series_form').attr('action', '{{base_url}}edit_series/' + $(this).data("no"));

		$("#series_title").html($(this).data("title"));
		$("#series_poster").attr("src", "{{base_url}}image_proxy" + $(this).data("poster"));

		$("#series_audio_language").html($(this).data("audio"));

		$('#series_languages').dropdown('clear');
		const languages_array = eval($(this).data("languages"));
		$('#series_languages').dropdown('set selected',languages_array);

		if ($(this).data("hearing-impaired") === "True") {
			$("#series_hearing-impaired_div").checkbox('check');
		} else {
			$("#series_hearing-impaired_div").checkbox('uncheck');
		}

		$('.small.modal').modal('show');
	});

	$('#series_languages').dropdown();

	$('.progress').progress({
		label: 'ratio',
		text: {
			ratio: '{value} / {total}'
		},
		showActivity: false
	});

	$( ".progress" ).each(function() {
		if ($(this).progress('is complete') !== true) {
			$(this).addClass('yellow');
		}
		if ($(this).progress('get total') == 0) {
			$(this).progress('update progress', '99');
			$(this).addClass('grey disabled');
			$(this).progress('set bar label', '0 / 0');
		}
	});
</script>