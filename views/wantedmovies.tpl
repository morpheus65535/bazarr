<html lang="en">
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
		
		<title>Wanted - Bazarr</title>
		
		<style>
			body {
				background-color: #272727;
			}
			#tablehistory {
				padding-top: 2em;
			}
			.fast.backward, .backward, .forward, .fast.forward {
    			cursor: pointer;
			}
			.fast.backward, .backward, .forward, .fast.forward { pointer-events: auto; }
			.fast.backward.disabled, .backward.disabled, .forward.disabled, .fast.forward.disabled { pointer-events: none; }
		</style>
	</head>
	<body>
		%import ast
		%from get_languages import *
		<div id='loader' class="ui page dimmer">
		   	<div id="loader_text" class="ui indeterminate text loader">Loading...</div>
		</div>

		<div class="ui container">
			<div class="ui right floated basic buttons">
				<button id="wanted_search_missing_subtitles_movies" class="ui button"><i class="download icon"></i>Download wanted subtitles</button>
			</div>
			<table id="tablehistory" class="ui very basic selectable table">
				<thead>
					<tr>
						<th>Movies</th>
						<th>Missing subtitles</th>
					</tr>
				</thead>
				<tbody>
				%import time
				%import pretty
				%if len(rows) == 0:
					<tr>
						<td colspan="2">No missing movie subtitles.</td>
					</tr>
				%end
                %for row in rows:
					<tr class="selectable">
						<td><a href="{{base_url}}movie/{{row[2]}}">{{row[0]}}</a></td>
						<td>
						<%
                        missing_languages = ast.literal_eval(row[1])
						if missing_languages is not None:
                            from get_subtitle import search_active
                            from config import settings
							for language in missing_languages:
                                if row[6] is not None and settings.general.getboolean('adaptive_searching') and language in row[6]:
                                        for lang in ast.literal_eval(row[6]):
                                            if language in lang:
                                                active = search_active(lang[1])
                                                if active:
                        %>
                                                    <a data-moviePath="{{row[3]}}" data-sceneName="{{row[5]}}" data-language="{{alpha3_from_alpha2(str(language))}}" data-hi="{{row[4]}}" data-radarrId={{row[2]}} ata-title="{{row[0].replace("'", "\'")}}" class="get_subtitle ui tiny label">
								                        {{language}}
                                                        <i style="margin-left:3px; margin-right:0" class="search icon"></i>
							                        </a>
                                                %else:
                                                    <a data-tooltip="Automatic searching delayed (adaptive search)" data-position="top right" data-inverted="" data-moviePath="{{row[3]}}" data-sceneName="{{row[5]}}" data-language="{{alpha3_from_alpha2(str(language))}}" data-hi="{{row[4]}}" data-radarrId={{row[2]}} ata-title="{{row[0].replace("'", "\'")}}" class="get_subtitle ui tiny label">
								                        {{language}}
                                                        <i style="margin-left:3px; margin-right:0" class="search red icon"></i>
							                        </a>
                                                %end
                                            %end
                                        %end
                                %else:
                                        <a data-moviePath="{{row[3]}}" data-sceneName="{{row[5]}}" data-language="{{alpha3_from_alpha2(str(language))}}" data-hi="{{row[4]}}" data-radarrId="{{row[2]}}" data-title="{{row[0].replace("'", "\'")}}" class="get_subtitle ui tiny label">
								            {{language}}
                                            <i style="margin-left:3px; margin-right:0" class="search icon"></i>
							            </a>
                                %end

							%end
						%end
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
			    		%if int(page) >= int(max_page):
			    		disabled\\
			    		%end
			    		 forward icon"></i>
			    		<i class="\\
			    		%if int(page) >= int(max_page):
			    		disabled\\
			    		%end
			    		 fast forward icon"></i>
			    	</div>
			    	<div class="right floated right aligned column">Total records: {{missing_count}}</div>
				</div>
			</div>
            %end
		</div>
	</body>
</html>


<script>
	$('a, button').on('click', function(){
		$('#loader').addClass('active');
	});

	$('.fast.backward').on('click', function(){
		loadURLmovies(1);
	});
	$('.backward:not(.fast)').on('click', function(){
		loadURLmovies({{int(page)-1}});
	});
	$('.forward:not(.fast)').on('click', function(){
		loadURLmovies({{int(page)+1}});
	});
	$('.fast.forward').on('click', function(){
		loadURLmovies({{int(max_page)}});
	});

	$('#wanted_search_missing_subtitles_movies').on('click', function(){
		$('#loader_text').text("Searching for missing subtitles...");
		window.location = '{{base_url}}wanted_search_missing_subtitles';
	});

	$('.get_subtitle').on('click', function(){
		    const values = {
		            moviePath: $(this).attr("data-moviePath"),
		            sceneName: $(this).attr("data-sceneName"),
		            language: $(this).attr("data-language"),
		            hi: $(this).attr("data-hi"),
		            radarrId: $(this).attr("data-radarrId"),
                    title: $(this).attr("data-title")
		    };
		    $('#loader_text').text("Downloading subtitles...");
			$('#loader').addClass('active');
		    $.ajax({
		        url: "{{base_url}}get_subtitle_movie",
		        type: "POST",
		        dataType: "json",
				data: values
		    }).always(function () {
				window.location.reload();
			});
	})
</script>