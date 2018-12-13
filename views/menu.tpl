<html>
    <head>
        <!DOCTYPE html>
		<link href="{{base_url}}static/noty/noty.css" rel="stylesheet">
		<script src="{{base_url}}static/noty/noty.min.js" type="text/javascript"></script>
		<style>
            #divmenu {
				background-color: #000000;
				padding-top: 2em;
				padding-bottom: 1em;
				padding-left: 1em;
				padding-right: 128px;
			}
			.prompt {
				background-color: #333333 !important;
				color: white !important;
				border-radius: 3px !important;
			}
			.searchicon {
				color: white !important;
			}
        </style>
    </head>
    <body>
		% from get_argv import config_dir

		% import os
		% import sqlite3
        % from get_settings import get_general_settings

        %if get_general_settings()[24] is True:
        %    monitored_only_query_string = ' AND monitored = "True"'
        %else:
        %    monitored_only_query_string = ""
        %end

        % conn = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    	% c = conn.cursor()
		% wanted_series = c.execute("SELECT COUNT(*) FROM table_episodes WHERE missing_subtitles != '[]'" + monitored_only_query_string).fetchone()
		% wanted_movies = c.execute("SELECT COUNT(*) FROM table_movies WHERE missing_subtitles != '[]'" + monitored_only_query_string).fetchone()

		<div id="divmenu" class="ui container">
			<div class="ui grid">
				<div class="middle aligned row">
					<div class="three wide column">
						<a href="{{base_url}}"><img class="logo" src="{{base_url}}static/logo128.png"></a>
					</div>

					<div class="twelve wide column">
						<div class="ui grid">
								<div class="row">
								<div class="sixteen wide column">
									<div class="ui inverted borderless labeled icon massive menu six item">
										<div class="ui container">
											% if get_general_settings()[12] is True:
											<a class="item" href="{{base_url}}series">
												<i class="play icon"></i>
												Series
											</a>
                                            % end
											% if get_general_settings()[13] is True:
											<a class="item" href="{{base_url}}movies">
												<i class="film icon"></i>
												Movies
											</a>
                                            % end
											<a class="item" href="{{base_url}}history">
												<i class="wait icon"></i>
												History
											</a>
											<a class="item" href="{{base_url}}wanted">
												<i class="warning sign icon">
													% if get_general_settings()[12] is True:
													<div class="floating ui tiny yellow label" style="left:90% !important;top:0.5em !important;">
														{{wanted_series[0]}}
													</div>
													% end
													% if get_general_settings()[13] is True:
													<div class="floating ui tiny green label" style="left:90% !important;top:3em !important;">
														{{wanted_movies[0]}}
													</div>
													% end
												</i>
												Wanted
											</a>
											<a class="item" href="{{base_url}}settings">
												<i class="settings icon"></i>
												Settings
											</a>
											<a class="item" href="{{base_url}}system">
												<i class="laptop icon"></i>
												System
											</a>
										</div>
									</div>
								</div>
							</div>

							<div style='padding-top:0rem;' class="row">
								<div class="three wide column"></div>

								<div class="ten wide column">
									<div class="ui search">
										<div class="ui left icon fluid input">
											<input class="prompt" type="text" placeholder="Search in your library">
											<i class="searchicon search icon"></i>
										</div>
									</div>
								</div>

								<div class="three wide column"></div>
							</div>
						</div>
                    </div>
                </div>
            </div>

			% restart_required = c.execute("SELECT configured, updated FROM system").fetchone()
			% c.close()

			% if restart_required[1] == '1' and restart_required[0] == '1':
			<div class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">Bazarr need to be restarted to apply last update and changes to general settings. Click <a href=# id="restart_link">here</a> to restart.</div></div></div>
			% elif restart_required[1] == '1':
				<div class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">Bazarr need to be restarted to apply last update. Click <a href=# id="restart_link">here</a> to restart.</div></div></div>
			% elif restart_required[0] == '1':
				<div class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">Bazarr need to be restarted to apply changes to general settings. Click <a href=# id="restart_link">here</a> to restart.</div></div></div>
			% end
		</div>
    </body>
</html>

<script>
    $('.ui.search')
        .search({
            apiSettings: {
                url: '{{base_url}}search_json/{query}',
                onResponse: function(results) {
                    var response = {
                        results : []
                    };
                    $.each(results.items, function(index, item) {
                        response.results.push({
                            title       : item.name,
                            url         : item.url
                        });
                    });
                    return response;
                }
            },
            minCharacters : 2
        })
    ;

    if (window.location.href.indexOf("episodes") > -1) {
    	$('.menu').css('background', '#000000');
    	$('.menu').css('opacity', '0.8');
    	$('#divmenu').css('background', '#000000');
    	$('#divmenu').css('opacity', '0.8');
    	$('#divmenu').css('box-shadow', '0px 0px 5px 5px #000000');
    }
    else if (window.location.href.indexOf("movie/") > -1) {
    	$('.menu').css('background', '#000000');
    	$('.menu').css('opacity', '0.8');
    	$('#divmenu').css('background', '#000000');
    	$('#divmenu').css('opacity', '0.8');
    	$('#divmenu').css('box-shadow', '0px 0px 5px 5px #000000');
    }
    else {
    	$('.menu').css('background', '#272727');
    	$('#divmenu').css('background', '#272727');
    }

    $('#restart_link').click(function(){
		$('#loader_text').text("Bazarr is restarting, please wait...");
		$.ajax({
			url: "{{base_url}}restart",
			async: true
		})
		.done(function(){
    		setTimeout(function(){ setInterval(ping, 2000); },8000);
		});
	})

	% from get_settings import get_general_settings
	% ip = get_general_settings()[0]
	% port = get_general_settings()[1]
	% base_url = get_general_settings()[2]

	if ("{{ip}}" == "0.0.0.0") {
		public_ip = window.location.hostname;
	} else {
		public_ip = "{{ip}}";
	}

	protocol = window.location.protocol;

	if (window.location.port == '{{current_port}}') {
	    public_port = '{{port}}';
    } else {
        public_port = window.location.port;
    }

	function ping() {
		$.ajax({
			url: protocol + '//' + public_ip + ':' + public_port + '{{base_url}}',
			success: function(result) {
				window.location.href= protocol + '//' + public_ip + ':' + public_port + '{{base_url}}';
			}
		});
	}
</script>

<script type="text/javascript">
    var ws = new WebSocket("ws://" + window.location.host + "{{base_url}}websocket");
    ws.onmessage = function (evt) {
        new Noty({
			text: evt.data,
			timeout: 3000,
			killer: true,
    		type: 'success',
			layout: 'bottomRight',
			theme: 'semanticui'
		}).show();
    };
</script>