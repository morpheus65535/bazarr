<html>
    <head>
        <!DOCTYPE html>
		<style>
            #divmenu {
				background-color: #272727;
				opacity: 0.9;
				padding-top: 2em;
				padding-bottom: 1em;
				padding-left: 1em;
				padding-right: 128px;
			}
			.icon {
				color: LightGray;
			}
			.prompt {
				background-color: #333333 !important;
				color: white !important;
				border-radius: 3px !important;
			}
        </style>
    </head>
    <body>
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
									<div style="background-color:#272727;" class="ui inverted borderless labeled icon massive menu five item">
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
												<i class="warning sign icon"></i>
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
											<i class="search icon"></i>
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
</script>