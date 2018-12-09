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
			#fondblanc {
				background-color: #ffffff;
				border-radius: 0;
				box-shadow: 0 0 5px 5px #ffffff;
				margin-top: 32px;
				margin-bottom: 3em;
				padding: 1em;
			}
		</style>
	</head>
	<body>
		% from get_argv import config_dir

		% import os
		% import sqlite3
		% from get_settings import get_general_settings

        %if get_general_settings()[24]:
        %    monitored_only_query_string = ' AND monitored = "True"'
        %else:
        %    monitored_only_query_string = ""
        %end

        % conn = sqlite3.connect(os.path.join(config_dir, 'db', 'bazarr.db'), timeout=30)
    	% c = conn.cursor()
		% wanted_series = c.execute("SELECT COUNT(*) FROM table_episodes WHERE missing_subtitles != '[]'" + monitored_only_query_string).fetchone()
		% wanted_movies = c.execute("SELECT COUNT(*) FROM table_movies WHERE missing_subtitles != '[]'" + monitored_only_query_string).fetchone()
		% c.close()

		<div id='loader' class="ui page dimmer">
		   	<div id="loader_text" class="ui indeterminate text loader">Loading...</div>
		</div>
		% include('menu.tpl')
			
		% import os

		<div id="fondblanc" class="ui container">
			<div class="ui top attached tabular menu">
				<a id="series_tab" class="tabs item active" data-enabled="{{get_general_settings()[12]}}" data-tab="series">Series
					<div class="ui tiny yellow label">
						{{wanted_series[0]}}
					</div>
				</a>
				<a id="movies_tab" class="tabs item" data-enabled="{{get_general_settings()[13]}}" data-tab="movies">Movies
					<div class="ui tiny green label">
						{{wanted_movies[0]}}
					</div>
				</a>
			</div>
			<div class="ui bottom attached tab segment" data-tab="series">
				<div class="content">
					<div id="content_series"></div>
				</div>
			</div>
			<div class="ui bottom attached tab segment" data-tab="movies">
				<div class="content">
					<div id="content_movies"></div>
				</div>
			</div>
		</div>
		% include('footer.tpl')
	</body>
</html>


<script>
	$('.menu .item')
		.tab()
	;

	$('#series_tab').on('click', function() {
	    loadURLseries(1);
	});

	$('#movies_tab').on('click', function() {
	    loadURLmovies(1);
	});

	function loadURLseries(page) {
		$.ajax({
	        url: "{{base_url}}wantedseries?page=" + page,
	        beforeSend: function() { $('#loader').addClass('active'); },
        	complete: function() { $('#loader').removeClass('active'); },
	        cache: false
	    }).done(function(data) {
	    	$("#content_series").html(data);
	    });
	}

	function loadURLmovies(page) {
		$.ajax({
	        url: "{{base_url}}wantedmovies?page=" + page,
	        beforeSend: function() { $('#loader').addClass('active'); },
        	complete: function() { $('#loader').removeClass('active'); },
	        cache: false
	    }).done(function(data) {
	    	$("#content_movies").html(data);
	    });
	}

	$('a:not(.tabs), button:not(.cancel, #download_log)').on('click', function(){
		$('#loader').addClass('active');
	});

	if ($('#series_tab').data("enabled") === "True") {
        $("#series_tab").removeClass('disabled');
    } else {
        $("#series_tab").addClass('disabled');
    }

    if ($('#movies_tab').data("enabled") === "True") {
        $("#movies_tab").removeClass('disabled');
    } else {
        $("#movies_tab").addClass('disabled');
    }
	if ($('#series_tab').data("enabled") === "True") {
        $( "#series_tab" ).trigger( "click" );
    }
    if ($('#series_tab').data("enabled") === "False" && $('#movies_tab').data("enabled") === "True") {
        $( "#movies_tab" ).trigger( "click" );
    }
</script>