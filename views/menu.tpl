<html>
    <head>
        <!DOCTYPE html>
		<style>
            #divmenu {
				background-color: #000000;
				opacity: 0.8;
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
		% import os
		% import sqlite3

		% conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    	% c = conn.cursor()
		% wanted = c.execute("SELECT COUNT(*) FROM table_episodes WHERE missing_subtitles != '[]'").fetchone()

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
									<div class="ui inverted borderless labeled icon massive menu five item">
										<div class="ui container">
											<a class="item" href="{{base_url}}">
												<i class="play icon"></i>
												Series
											</a>
											<a class="item" href="{{base_url}}history">
												<i class="wait icon"></i>
												History
											</a>
											<a class="item" href="{{base_url}}wanted">
												<i class="warning sign icon">
												% if wanted[0] > 0:
													<div class="floating ui tiny yellow label">
														{{wanted[0]}}
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
											<input class="prompt" type="text" placeholder="Search the series in your library">
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
		</div>

    	% restart_required = c.execute("SELECT updated, configured FROM table_settings_general").fetchone()
    	% conn.commit()
    	% c.close()

		% if restart_required[0] == 1 and restart_required[1] == 1:
			<div class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">Bazarr need to be restarted to apply last update and changes to general settings.</div></div></div>
		% elif restart_required[0] == 1:
			<div class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">Bazarr need to be restarted to apply last update.</div></div></div>
		% elif restart_required[1] == 1:
			<div class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">Bazarr need to be restarted to apply changes to general settings.</div></div></div>
		% end
    </body>
</html>

<script>
    $('.ui.search')
        .search({
            apiSettings: {
                url: '{{base_url}}series_json/{query}',
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
    	$('#divmenu').css('background', '#000000');
    }
    else {
    	$('.menu').css('background', '#272727');
    	$('#divmenu').css('background', '#272727');
    }
</script>