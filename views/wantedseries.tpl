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
		
		<title>Wanted - Bazarr</title>
		
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
		%import pycountry
		<div id='loader' class="ui page dimmer">
		   	<div class="ui indeterminate text loader">Loading...</div>
		</div>

		<div class="ui container">
			<div class="ui right floated basic buttons">
				<button id="wanted_search_missing_subtitles" class="ui button"><i class="download icon"></i>Download wanted subtitles</button>
			</div>
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
				%if len(rows) == 0:
					<tr>
						<td colspan="4">No missing episode subtitles.</td>
					</tr>
				%end
				%for row in rows:
					<tr class="selectable">
						<td><a href="{{base_url}}episodes/{{row[4]}}">{{row[0]}}</a></td>
						<td class="collapsing">
							<%episode = row[1].split('x')%>
							{{episode[0] + 'x' + episode[1].zfill(2)}}
						</td>
						<td>{{row[2]}}</td>
						<td>
						%missing_languages = ast.literal_eval(row[3])
						%if missing_languages is not None:
							%for language in missing_languages:
							<a data-episodePath="{{row[5]}}" data-sceneName="{{row[8]}}" data-language="{{pycountry.languages.lookup(str(language)).alpha_3}}" data-hi="{{row[6]}}" data-sonarrSeriesId={{row[4]}} data-sonarrEpisodeId={{row[7]}} class="get_subtitle ui tiny label">
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
	</body>
</html>


<script>
	$('a, button').click(function(){
		$('#loader').addClass('active');
	})

	$('.fast.backward').click(function(){
		loadURLseries(1);
	})
	$('.backward:not(.fast)').click(function(){
		loadURLseries({{int(page)-1}});
	})
	$('.forward:not(.fast)').click(function(){
		loadURLseries({{int(page)+1}});
	})
	$('.fast.forward').click(function(){
		loadURLseries({{int(max_page)}});
	})

	$('#wanted_search_missing_subtitles').click(function(){
		window.location = '{{base_url}}wanted_search_missing_subtitles';
	})

	$('.get_subtitle').click(function(){
		    var values = {
		            episodePath: $(this).attr("data-episodePath"),
		            sceneName: $(this).attr("data-sceneName"),
		            language: $(this).attr("data-language"),
		            hi: $(this).attr("data-hi"),
		            sonarrSeriesId: $(this).attr("data-sonarrSeriesId"),
		            sonarrEpisodeId: $(this).attr("data-sonarrEpisodeId")
		    };
		    $('#loader').addClass('active');
		    $.ajax({
		        url: "{{base_url}}get_subtitle",
		        type: "POST",
		        dataType: "json",
				data: values
		    }).always(function () {
				window.location.reload();
			});
	})
</script>