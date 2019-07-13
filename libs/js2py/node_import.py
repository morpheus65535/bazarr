__all__ = ['require']
import subprocess, os, codecs, glob
from .evaljs import translate_js
import six
DID_INIT = False
DIRNAME = os.path.dirname(os.path.abspath(__file__))
PY_NODE_MODULES_PATH = os.path.join(DIRNAME, 'py_node_modules')


def _init():
    global DID_INIT
    if DID_INIT:
        return
    assert subprocess.call(
        'node -v', shell=True, cwd=DIRNAME
    ) == 0, 'You must have node installed! run: brew install node'
    assert subprocess.call(
        'cd %s;npm install babel-core babel-cli babel-preset-es2015 babel-polyfill babelify browserify'
        % repr(DIRNAME),
        shell=True,
        cwd=DIRNAME) == 0, 'Could not link required node_modules'
    DID_INIT = True


ADD_TO_GLOBALS_FUNC = '''
;function addToGlobals(name, obj) {
    if (!Object.prototype.hasOwnProperty('_fake_exports')) {
        Object.prototype._fake_exports = {};
    }
    Object.prototype._fake_exports[name] = obj;
};

'''
# subprocess.call("""node -e 'require("browserify")'""", shell=True)
GET_FROM_GLOBALS_FUNC = '''
;function getFromGlobals(name) {
    if (!Object.prototype.hasOwnProperty('_fake_exports')) {
        throw Error("Could not find any value named "+name);
    }
    if (Object.prototype._fake_exports.hasOwnProperty(name)) {
        return Object.prototype._fake_exports[name];
    } else {
        throw Error("Could not find any value named "+name);
    }
};

'''


def require(module_name, include_polyfill=False, update=False):
    assert isinstance(module_name, str), 'module_name must be a string!'
    py_name = module_name.replace('-', '_')
    module_filename = '%s.py' % py_name
    var_name = py_name.rpartition('/')[-1]
    if not os.path.exists(os.path.join(PY_NODE_MODULES_PATH,
                                       module_filename)) or update:
        _init()
        in_file_name = 'tmp0in439341018923js2py.js'
        out_file_name = 'tmp0out439341018923js2py.js'
        code = ADD_TO_GLOBALS_FUNC
        if include_polyfill:
            code += "\n;require('babel-polyfill');\n"
        code += """
        var module_temp_love_python = require(%s);
        addToGlobals(%s, module_temp_love_python);
        """ % (repr(module_name), repr(module_name))
        with open(os.path.join(DIRNAME, in_file_name), 'wb') as f:
            f.write(code.encode('utf-8') if six.PY3 else code)

        pkg_name = module_name.partition('/')[0]
        # make sure the module is installed
        assert subprocess.call(
            'cd %s;npm install %s' % (repr(DIRNAME), pkg_name),
            shell=True,
            cwd=DIRNAME
        ) == 0, 'Could not install the required module: ' + pkg_name

        # convert the module
        assert subprocess.call(
            '''node -e "(require('browserify')('./%s').bundle(function (err,data) {fs.writeFile('%s', require('babel-core').transform(data, {'presets': require('babel-preset-es2015')}).code, ()=>{});}))"'''
            % (in_file_name, out_file_name),
            shell=True,
            cwd=DIRNAME,
        ) == 0, 'Error when converting module to the js bundle'

        os.remove(os.path.join(DIRNAME, in_file_name))
        with codecs.open(os.path.join(DIRNAME, out_file_name), "r",
                         "utf-8") as f:
            js_code = f.read()
        os.remove(os.path.join(DIRNAME, out_file_name))

        js_code += GET_FROM_GLOBALS_FUNC
        js_code += ';var %s = getFromGlobals(%s);%s' % (
            var_name, repr(module_name), var_name)
        print('Please wait, translating...')
        py_code = translate_js(js_code)

        dirname = os.path.dirname(
            os.path.join(PY_NODE_MODULES_PATH, module_filename))
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        with open(os.path.join(PY_NODE_MODULES_PATH, module_filename),
                  'wb') as f:
            f.write(py_code.encode('utf-8') if six.PY3 else py_code)
    else:
        with codecs.open(
                os.path.join(PY_NODE_MODULES_PATH, module_filename), "r",
                "utf-8") as f:
            py_code = f.read()

    context = {}
    exec (py_code, context)
    return context['var'][var_name].to_py()
