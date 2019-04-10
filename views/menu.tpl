<html lang="en">
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
            div.disabled { pointer-events: none; }
            button.disabled { pointer-events: none; }
        </style>
    </head>
    <body>
		% from get_args import args
		% from get_providers import update_throttled_provider
		% update_throttled_provider()

		% import ast
		% import datetime
		% import os
		% import sqlite3
        % from config import settings

        %if settings.sonarr.getboolean('only_monitored'):
        %    monitored_only_query_string_sonarr = ' AND monitored = "True"'
        %else:
        %    monitored_only_query_string_sonarr = ""
        %end

        %if settings.radarr.getboolean('only_monitored'):
        %    monitored_only_query_string_radarr = ' AND monitored = "True"'
        %else:
        %    monitored_only_query_string_radarr = ""
        %end

        % conn = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    	% c = conn.cursor()
		% wanted_series = c.execute("SELECT COUNT(*) FROM table_episodes WHERE missing_subtitles != '[]'" + monitored_only_query_string_sonarr).fetchone()
		% wanted_movies = c.execute("SELECT COUNT(*) FROM table_movies WHERE missing_subtitles != '[]'" + monitored_only_query_string_radarr).fetchone()
		% from get_providers import list_throttled_providers
		% throttled_providers_count = len(eval(str(settings.general.throtteled_providers)))
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
									<div class="ui inverted borderless labeled icon massive menu seven item">
										<div class="ui container">
											% if settings.general.getboolean('use_sonarr'):
											<a class="item" href="{{base_url}}series">
												<i class="play icon"></i>
												Series
											</a>
                                            % end
											% if settings.general.getboolean('use_radarr'):
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
													% if settings.general.getboolean('use_sonarr'):
													<div class="floating ui tiny yellow label" style="left:90% !important;top:0.5em !important;">
														{{wanted_series[0]}}
													</div>
													% end
													% if settings.general.getboolean('use_radarr'):
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
												<i class="laptop icon">
													% if throttled_providers_count:
													<div class="floating ui tiny yellow label" style="left:90% !important;top:0.5em !important;">
														{{throttled_providers_count}}
													</div>
													% end
												</i>
												System
											</a>
											<a id="donate" class="item" href="https://beerpay.io/morpheus65535/bazarr">
												<i class="red heart icon"></i>
												Donate
											</a>
										</div>
									</div>
								</div>
							</div>

							<div style='padding-top:0;' class="row">
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
                    const response = {
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
    	$('#divmenu').css('box-shadow', '0 0 5px 5px #000000');
    }
    else if (window.location.href.indexOf("movie/") > -1) {
    	$('.menu').css('background', '#000000');
    	$('.menu').css('opacity', '0.8');
    	$('#divmenu').css('background', '#000000');
    	$('#divmenu').css('opacity', '0.8');
    	$('#divmenu').css('box-shadow', '0 0 5px 5px #000000');
    }
    else {
    	$('.menu').css('background', '#272727');
    	$('#divmenu').css('background', '#272727');
    }

    $('#restart_link').on('click', function(){
		$('#loader_text').text("Bazarr is restarting, please wait...");
		$.ajax({
			url: "{{base_url}}restart",
			async: true
		})
		.done(function(){
    		setTimeout(function(){ setInterval(ping, 2000); },8000);
		});
	});

	% from config import settings
    % from get_args import args
	% ip = settings.general.ip
	% port = args.port if args.port else settings.general.port
	% base_url = settings.general.base_url

	if ("{{ip}}" === "0.0.0.0") {
		public_ip = window.location.hostname;
	} else {
		public_ip = "{{ip}}";
	}

	protocol = window.location.protocol;

	if (window.location.port === '{{current_port}}') {
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
	var url_notifications = location.protocol +"//" + window.location.host + "{{base_url}}notifications";
	var notificationTimeout;
	var timeout;
	var killer;
	function doNotificationsAjax() {
        $.ajax({
            url: url_notifications,
            success: function (data) {
            	if (data !== "") {
                    data = JSON.parse(data);
                    var msg = data[0];
                    var type = data[1];
                    var duration = data[2];
                    var button = data[3];
                    var queue = data[4];

                    if (duration === 'temporary') {
                        timeout = 3000;
                        killer = queue;
                    } else if (duration === 'long') {
                        timeout = 15000;
                        killer = queue;
                    }  else {
						timeout = false;
						killer = false;
					}

					if (button === 'refresh') {
						button = [ Noty.button('Refresh', 'ui tiny primary button', function () { window.location.reload() }) ];
					} else if (button === 'restart') {
						// to be completed
						button = [ Noty.button('Restart', 'ui tiny primary button', function () { alert('Restart not implemented yet!') }) ];
					} else {
						button = [];
					}

					new Noty({
						text: msg,
						progressBar: false,
						animation: {
							open: null,
							close: null
						},
						type: type,
						layout: 'bottomRight',
						theme: 'semanticui',
						queue: queue,
						timeout: timeout,
							killer: killer,
						buttons: button,
						force: true
					}).show();
				}
            },
            complete: function (data) {
                // Schedule the next
                if (data !== "") {
                	notificationTimeout = setTimeout(doNotificationsAjax, 100);
				} else {
                	notificationTimeout = setTimeout(doNotificationsAjax, 1000);
				}
            }
        });
    }
    notificationTimeout = setTimeout(doNotificationsAjax, 1000);

	$(window).bind('beforeunload', function(){
		clearTimeout(notificationTimeout);
	});
</script>


<script type="text/javascript">
	var url_tasks = location.protocol +"//" + window.location.host + "{{base_url}}running_tasks";
	var tasksTimeout;
	function doTasksAjax() {
        $.ajax({
            url: url_tasks,
            dataType: 'json',
            success: function (data) {
            	$('#tasks > tbody  > tr').each(function() {
					if ($.inArray($(this).attr('id'), data['tasks']) > -1) {
					    $(this).find('td:last').find('div:first').addClass('disabled');
						$(this).find('td:last').find('div:first').find('i:first').addClass('loading');
					} else {
						$(this).find('td:last').find('div:first').removeClass('disabled');
						$(this).find('td:last').find('div:first').find('i:first').removeClass('loading');
					}
				});

            	if ($.inArray('wanted_search_missing_subtitles', data['tasks']) > -1) {
                    $('#wanted_search_missing_subtitles').addClass('disabled');
                    $('#wanted_search_missing_subtitles_movies').addClass('disabled');
                    $('#wanted_search_missing_subtitles').find('i:first').addClass('loading');
                    $('#wanted_search_missing_subtitles_movies').find('i:first').addClass('loading');
                } else {
                    $('#wanted_search_missing_subtitles').removeClass('disabled');
                    $('#wanted_search_missing_subtitles_movies').removeClass('disabled');
                    $('#wanted_search_missing_subtitles').find('i:first').removeClass('loading');
                    $('#wanted_search_missing_subtitles_movies').find('i:first').removeClass('loading');
                }

                %if 'no' in locals():
            	if ($.inArray('search_missing_subtitles_{{no}}', data['tasks']) > -1) {
                    $('#search_missing_subtitles').addClass('disabled');
                    $('#search_missing_subtitles').find('i:first').addClass('loading');
                } else {
                    $('#search_missing_subtitles').removeClass('disabled');
                    $('#search_missing_subtitles').find('i:first').removeClass('loading');
                }

            	if ($.inArray('search_missing_subtitles_movie_{{no}}', data['tasks']) > -1) {
                    $('#search_missing_subtitles_movie').addClass('disabled');
                    $('#search_missing_subtitles_movie').find('i:first').addClass('loading');
                } else {
                    $('#search_missing_subtitles_movie').removeClass('disabled');
                    $('#search_missing_subtitles_movie').find('i:first').removeClass('loading');
                }
            	%end
            },
            complete: function (data) {
                // Schedule the next
                tasksTimeout = setTimeout(doTasksAjax, 5000);
            }
        });
    }
    tasksTimeout = setTimeout(doTasksAjax, 500);

	$(window).bind('beforeunload', function(){
		clearTimeout(tasksTimeout);
	});
</script>