                <div class="ui dividing header">Subtitles providers</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Addic7ed (require anti-captcha)</label>
                            </div>
                            <div class="one wide column">
                                <div id="addic7ed" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="addic7ed_option" class="ui grid container">
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Username</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_addic7ed_username" type="text" value="{{settings.addic7ed.username if settings.addic7ed.username != None else ''}}">
                                    </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Password</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_addic7ed_password" type="password" value="{{settings.addic7ed.password if settings.addic7ed.password != None else ''}}">
                                    </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Random user-agents</label>
                                </div>
                                <div class="one wide column">
                                    <div id="settings_addic7ed_random_agents" class="ui toggle checkbox" data-randomagents={{settings.addic7ed.getboolean('random_agents')}}>
                                        <input type="checkbox" name="settings_addic7ed_random_agents">
                                        <label></label>
                                    </div>
                                </div>
                                <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Use random user agents" data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Argenteam</label>
                            </div>
                            <div class="one wide column">
                                <div id="argenteam" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Spanish subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="argenteam_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Assrt</label>
                            </div>
                            <div class="one wide column">
                                <div id="assrt" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Chinese subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="assrt_option" class="ui grid container">
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Token</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_assrt_token" type="text" value="{{settings.assrt.token if settings.assrt.token != None else ''}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>BetaSeries</label>
                            </div>
                            <div class="one wide column">
                                <div id="betaseries" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="French/English provider for TV Shows only." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="This provider only uses the subtitle filename to find release group matches, subtitles may thus be out of sync." data-inverted="">
                                        <i class="yellow warning sign icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="betaseries_option" class="ui grid container">
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Token/Secret Key</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_betaseries_token" type="text" value="{{settings.betaseries.token if settings.betaseries.token != None else ''}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>GreekSubtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="greeksubtitles" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Greek subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="greeksubtitles_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Hosszupuska</label>
                            </div>
                            <div class="one wide column">
                                <div id="hosszupuska" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Hungarian subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="hosszupuska_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Nekur</label>
                            </div>
                            <div class="one wide column">
                                <div id="nekur" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Latvian subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="nekur_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>LegendasTV</label>
                            </div>
                            <div class="one wide column">
                                <div id="legendastv" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Brazilian Portuguese subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="legendastv_option" class="ui grid container">
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Username</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_legendastv_username" type="text" value="{{settings.legendastv.username if settings.legendastv.username != None else ''}}">
                                    </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Password</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_legendastv_password" type="password" value="{{settings.legendastv.password if settings.legendastv.password != None else ''}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Napiprojekt</label>
                            </div>
                            <div class="one wide column">
                                <div id="napiprojekt" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Polish subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="napiprojekt_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Napisy24</label>
                            </div>
                            <div class="one wide column">
                                <div id="napisy24" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Polish subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="napisy24_option" class="ui grid container">
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Username</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_napisy24_username" type="text" value="{{settings.napisy24.username if settings.napisy24.username != None else ''}}">
                                    </div>
                                </div>
                                <div class="collapsed column">
                                    <div class="collapsed center aligned column">
                                        <div data-tooltip="The provided credentials must have api access. Leave empty to use the defaults." data-inverted="" class="ui basic icon">
                                            <i class="yellow warning circle large icon"></i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Password</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_napisy24_password" type="password" value="{{settings.napisy24.password if settings.napisy24.password != None else ''}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>OpenSubtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="opensubtitles" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="opensubtitles_option" class="ui grid container">
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Username</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_opensubtitles_username" type="text" value="{{settings.opensubtitles.username if settings.opensubtitles.username != None else ''}}">
                                    </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Password</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_opensubtitles_password" type="password" value="{{settings.opensubtitles.password if settings.opensubtitles.password != None else ''}}">
                                    </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>VIP</label>
                                </div>
                                <div class="one wide column">
                                    <div id="settings_opensubtitles_vip" class="ui toggle checkbox" data-osvip={{settings.opensubtitles.getboolean('vip')}}>
                                        <input type="checkbox" name="settings_opensubtitles_vip">
                                        <label></label>
                                    </div>
                                </div>
                                <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="ad-free subs, 1000 subs/day, no-cache VIP server: http://v.ht/osvip" data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Use SSL</label>
                                </div>
                                <div class="one wide column">
                                    <div id="settings_opensubtitles_ssl" class="ui toggle checkbox" data-osssl={{settings.opensubtitles.getboolean('ssl')}}>
                                        <input type="checkbox" name="settings_opensubtitles_ssl">
                                        <label></label>
                                    </div>
                                </div>
                                <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Use SSL to connect to OpenSubtitles" data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Skip wrong FPS</label>
                                </div>
                                <div class="one wide column">
                                    <div id="settings_opensubtitles_skip_wrong_fps" class="ui toggle checkbox" data-osfps={{settings.opensubtitles.getboolean('skip_wrong_fps')}}>
                                        <input type="checkbox" name="settings_opensubtitles_skip_wrong_fps">
                                        <label></label>
                                    </div>
                                </div>
                                <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Skip subtitles with a mismatched FPS value; might lead to more results when disabled but also to more false-positives." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Podnapisi</label>
                            </div>
                            <div class="one wide column">
                                <div id="podnapisi" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="podnapisi_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subdivx</label>
                            </div>
                            <div class="one wide column">
                                <div id="subdivx" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Spanish subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subdivx_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subs.sab.bz</label>
                            </div>
                            <div class="one wide column">
                                <div id="subssabbz" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Bulgarian mostly subtitle provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subssabbz_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subscene (require anti-captcha)</label>
                            </div>
                            <div class="one wide column">
                                <div id="subscene" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>

                            <div id="subscene_option" class="ui grid container">
                                <div class="middle aligned row">
                                    <div class="right aligned six wide column">
                                        <label>Username</label>
                                    </div>
                                    <div class="six wide column">
                                        <div class="ui fluid input">
                                            <input name="settings_subscene_username" type="text" value="{{settings.subscene.username if settings.subscene.username != None else ''}}">
                                        </div>
                                    </div>
                                </div>
                                <div class="middle aligned row">
                                    <div class="right aligned six wide column">
                                        <label>Password</label>
                                    </div>
                                    <div class="six wide column">
                                        <div class="ui fluid input">
                                            <input name="settings_subscene_password" type="password" value="{{settings.subscene.password if settings.subscene.password != None else ''}}">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subscenter</label>
                            </div>
                            <div class="one wide column">
                                <div id="subscenter" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="subscenter_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subsunacs.net</label>
                            </div>
                            <div class="one wide column">
                                <div id="subsunacs" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Bulgarian mostly subtitle provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subsunacs_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subs4Free</label>
                            </div>
                            <div class="one wide column">
                                <div id="subs4free" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Greek subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subs4free_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Subs4Series</label>
                            </div>
                            <div class="one wide column">
                                <div id="subs4series" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Greek subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subs4series_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>subtitri.id.lv</label>
                            </div>
                            <div class="one wide column">
                                <div id="subtitriid" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Latvian subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subtitriid_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>SubZ</label>
                            </div>
                            <div class="one wide column">
                                <div id="subz" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Greek subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="subz_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Supersubtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="supersubtitles" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="supersubtitles_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Titlovi (require anti-captcha)</label>
                            </div>
                            <div class="one wide column">
                                <div id="titlovi" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="titlovi_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>TVSubtitles</label>
                            </div>
                            <div class="one wide column">
                                <div id="tvsubtitles" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                        </div>
                        <div id="tvsubtitles_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>XSubs</label>
                            </div>
                            <div class="one wide column">
                                <div id="xsubs" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Greek subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="xsubs_option" class="ui grid container">
                        	<div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Username</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_xsubs_username" type="text" value="{{settings.xsubs.username if settings.xsubs.username != None else ''}}">
                                    </div>
                                </div>
                            </div>
                            <div class="middle aligned row">
                                <div class="right aligned six wide column">
                                    <label>Password</label>
                                </div>
                                <div class="six wide column">
                                    <div class="ui fluid input">
                                        <input name="settings_xsubs_password" type="password" value="{{settings.xsubs.password if settings.xsubs.password != None else ''}}">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Zimuku</label>
                            </div>
                            <div class="one wide column">
                                <div id="zimuku" class="ui toggle checkbox provider">
                                    <input type="checkbox">
                                    <label></label>
                                </div>
                            </div>
                            <div class="collapsed column">
                                <div class="collapsed center aligned column">
                                    <div class="ui basic icon" data-tooltip="Chinese subtitles provider." data-inverted="">
                                        <i class="help circle large icon"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="zimuku_option" class="ui grid container">

                        </div>

                        <div class="middle aligned row">
                            <div class="eleven wide column">
                                <div class='field' hidden>
                                    <select name="settings_subliminal_providers" id="settings_providers" multiple="" class="ui fluid search selection dropdown">
                                        <option value="">Providers</option>
                                        %enabled_providers = []
                                        %providers = settings.general.enabled_providers.lower().split(',')
                                        %for provider in settings_providers:
                                        <option value="{{provider}}">{{provider}}</option>
                                        %end
                                        %for provider in providers:
                                        %enabled_providers.append(str(provider))
                                        %end
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                    if ($('#settings_addic7ed_random_agents').data("randomagents") === "True") {
                        $("#settings_addic7ed_random_agents").checkbox('check');
                    } else {
                        $("#settings_addic7ed_random_agents").checkbox('uncheck');
                    }

                    if ($('#settings_opensubtitles_vip').data("osvip") === "True") {
                        $("#settings_opensubtitles_vip").checkbox('check');
                    } else {
                        $("#settings_opensubtitles_vip").checkbox('uncheck');
                    }

                    if ($('#settings_opensubtitles_ssl').data("osssl") === "True") {
                        $("#settings_opensubtitles_ssl").checkbox('check');
                    } else {
                        $("#settings_opensubtitles_ssl").checkbox('uncheck');
                    }

                    if ($('#settings_opensubtitles_skip_wrong_fps').data("osfps") === "True") {
                        $("#settings_opensubtitles_skip_wrong_fps").checkbox('check');
                    } else {
                        $("#settings_opensubtitles_skip_wrong_fps").checkbox('uncheck');
                    }

                    $('#settings_providers').dropdown('clear');
                    $('#settings_providers').dropdown('set selected',{{!enabled_providers}});
                    $('#settings_providers').dropdown();

                    $('#settings_providers').dropdown('setting', 'onChange', function(){
                        $('.form').form('validate field', 'settings_subliminal_providers');
                    });

                    $("#settings_providers > option").each(function() {
                        $('#'+$(this).val()+'_option').hide();
                    });

                    $("#settings_providers > option:selected").each(function() {
                        $('[id='+this.value+']').checkbox('check');
                        $('#'+$(this).val()+'_option').show();
                    });

                    $('.provider').checkbox({
                        onChecked: function() {
                            $('#settings_providers').dropdown('set selected', $(this).parent().attr('id'));
                            $('#'+$(this).parent().attr('id')+'_option').show();
                        },
                        onUnchecked: function() {
                            $('#settings_providers').dropdown('remove selected', $(this).parent().attr('id'));
                            $('#'+$(this).parent().attr('id')+'_option').hide();
                        }
                    });
                </script>
