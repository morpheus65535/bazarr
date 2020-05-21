/**
 * @summary altEditor
 * @description Lightweight editor for DataTables
 * @version 2.0
 * @file dataTables.editor.free.js
 * @author kingkode (www.kingkode.com)
 *  Modified by: Kasper Olesen (https://github.com/KasperOlesen), Luca Vercelli (https://github.com/luca-vercelli), Zack Hable (www.cobaltdevteam.com)
 * @contact www.kingkode.com/contact
 * @contact zack@cobaltdevteam.com
 * @copyright Copyright 2016 Kingkode
 *
 * This source file is free software, available under the following license: MIT
 * license
 *
 * This source file is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the license files for details.
 *
 *
 */
(function (factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD
        define(['jquery', 'datatables.net'], function ($) {
            return factory($, window, document);
        });
    }
    else if (typeof exports === 'object') {
        // CommonJS
        module.exports = function (root, $) {
            if (!root) {
                root = window;
            }

            if (!$ || !$.fn.dataTable) {
                $ = require('datatables.net')(root, $).$;
            }

            return factory($, root, root.document);
        };
    }
    else {
        // Browser
        factory(jQuery, window, document);
    }
})
(function ($, window, document, undefined) {
    'use strict';
    var DataTable = $.fn.dataTable;

    var _instance = 0;

    /**
     * altEditor provides modal editing of records for Datatables
     *
     * @class altEditor
     * @constructor
     * @param {object}
     *            oTD DataTables settings object
     * @param {object}
     *            oConfig Configuration object for altEditor
     */
    var altEditor = function (dt, opts) {
        if (!DataTable.versionCheck || !DataTable.versionCheck('1.10.8')) {
            throw ("Warning: altEditor requires DataTables 1.10.8 or greater");
        }

        // User and defaults configuration object
        this.c = $.extend(true, {}, DataTable.defaults.altEditor,
            altEditor.defaults, opts);

        /**
         * @namespace Settings object which contains customisable information
         *            for altEditor instance
         */
        this.s = {
            /** @type {DataTable.Api} DataTables' API instance */
            dt: new DataTable.Api(dt),

            /** @type {String} Unique namespace for events attached to the document */
            namespace: '.altEditor' + (_instance++)
        };

        /**
         * @namespace Common and useful DOM elements for the class instance
         */
        this.dom = {
            /** @type {jQuery} altEditor handle */
            modal: $('<div class="dt-altEditor-handle"/>'),
        };

        /* Constructor logic */
        this._constructor();
    }

    $.extend(
        altEditor.prototype,
        {
            /***************************************************************
             * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
             * Constructor * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
             */

            /**
             * Initialise the RowReorder instance
             *
             * @private
             */
            _constructor: function () {
                var that = this;
                var dt = this.s.dt;

                if (dt.settings()[0].oInit.onAddRow)
                    that.onAddRow = dt.settings()[0].oInit.onAddRow;
                if (dt.settings()[0].oInit.onDeleteRow)
                    that.onDeleteRow = dt.settings()[0].oInit.onDeleteRow;
                if (dt.settings()[0].oInit.onEditRow)
                    that.onEditRow = dt.settings()[0].oInit.onEditRow;

                this._setup();

                dt.on('destroy.altEditor', function () {
                    dt.off('.altEditor');
                    $(dt.table().body()).off(that.s.namespace);
                    $(document.body).off(that.s.namespace);
                });
            },

            /***************************************************************
             * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
             * Private methods * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
             */

            /**
             * Setup dom and bind button actions
             *
             * @private
             */
            _setup: function () {
                var that = this;
                var dt = this.s.dt;
                this.random_id = ("" + Math.random()).replace(".", "");
                var modal_id = `altEditor-modal-${this.random_id}`;
                this.modal_selector = '#' + modal_id;
                this.language = DataTable.settings.values().next().value.oLanguage.altEditor || {};
                this.language.modalClose = this.language.modalClose || 'Close';
                this.language.edit = this.language.edit || {};
                this.language.edit = { title: this.language.edit.title || 'Edit record',
                                       button: this.language.edit.button || 'Edit'
                                     };
                this.language.delete = this.language.delete || {};
                this.language.delete = { title: this.language.delete.title || 'Delete record',
                                         button: this.language.delete.button || 'Delete' };
                this.language.add = this.language.add || {};
                this.language.add = { title: this.language.add.title || 'Add record',
                                      button: this.language.add.button || 'Add'
                                    };
                this.language.success = this.language.success || 'Success!';
                this.language.error = this.language.error || {};
                this.language.error = { message: this.language.error.message || 'There was an unknown error!',
                                        label: this.language.error.label || 'Error!',
                                        responseCode: this.language.error.responseCode || 'Response code: ',
                                        required: this.language.error.required || 'Field is required',
                                        unique: this.language.error.unique || 'Duplicated field'
                                      };
                var modal = '<div class="modal fade" id="' + modal_id + '" tabindex="-1" role="dialog">' +
                    '<div class="modal-dialog">' +
                    '<div class="modal-content">' +
                    '<div class="modal-header">' +
                    '<h4 style="padding-top: 1rem;padding-left: 1rem;" class="modal-title"></h4>' +
                    '<button style="margin: initial;" type="button" class="close" data-dismiss="modal" aria-label="' + this.language.modalClose + '">' +
                    '<span aria-hidden="true">&times;</span></button>' +
                    '</div>' +
                    '<div class="modal-body">' +
                    '<p></p>' +
                    '</div>' +
                    '<div class="modal-footer">' +
                    '</div>' +
                    '</div>' +
                    '</div>' +
                    '</div>';
                // add modal
                $('body').append(modal);

                // add Edit Button
                if (dt.button('edit:name')) {
                    dt.button('edit:name').action(function (e, dt, node, config) {
                        that._openEditModal();

                        $(`#altEditor-edit-form-${that.random_id}`)
                        .off('submit')
                        .on('submit', function (e) {
                            e.preventDefault();
                            e.stopPropagation();
                            that._editRowData();
                        });
                    });
                }

                // add Delete Button
                if (dt.button('delete:name')) {
                    dt.button('delete:name').action(function (e, dt, node, config) {
                        that._openDeleteModal();

                        $(`#altEditor-delete-form-${that.random_id}`)
                        .off('submit')
                        .on('submit', function (e) {
                            e.preventDefault();
                            e.stopPropagation();
                            that._deleteRow();
                        });
                    });
                }

                // add Add Button
                if (dt.button('add:name')) {
                    dt.button('add:name').action(function (e, dt, node, config) {
                        that._openAddModal();

                        $(`#altEditor-add-form-${that.random_id}`)
                        .off('submit')
                        .on('submit', function (e) {
                            e.preventDefault();
                            e.stopPropagation();
                            that._addRowData();
                        });
                    });
                }
                
                // bind 'unique' error messages
                $(this.modal_selector).bind('input', '[data-unique]', function(elm) {
                    if ($(elm.target).attr('data-unique') == null || $(elm.target).attr('data-unique') === 'false') {
                        return;
                    }
                    var target = $(elm.target);
                    var colData = dt.column("th:contains('" + target.attr("name") + "')").data();
                    // go through each item in this column
                    var selectedCellData = null;
                    if (dt.row({selected: true}).index() != null)
                        selectedCellData = dt.cell(dt.row({selected: true}).index(), dt.column("th:contains('" + target.attr("name") + "')").index()).data();
                    elm.target.setCustomValidity('');
                    for (var j in colData) {
                        // if the element is in the column and its not the selected one then its not unique
                        if (target.val() == colData[j] && colData[j] != selectedCellData) {
                            elm.target.setCustomValidity(that.language.error.unique);
                        }
                    }
                });
                        
                // add Refresh button
                if (this.s.dt.button('refresh:name')) {
                    this.s.dt.button('refresh:name').action(function (e, dt, node, config) {
                        if (dt.ajax && dt.ajax.url()) {
                            dt.ajax.reload();
                        }
                    });
                }
            },

            /**
             * Emit an event on the DataTable for listeners
             *
             * @param {string}
             *            name Event name
             * @param {array}
             *            args Event arguments
             * @private
             */
            _emitEvent: function (name, args) {
                this.s.dt.iterator('table', function (ctx, i) {
                    $(ctx.nTable).triggerHandler(name + '.dt', args);
                });
            },

            /**
             * Open Edit Modal for selected row
             *
             * @private
             */
            _openEditModal: function () {
                
                var dt = this.s.dt;
                var adata = dt.rows({
                    selected: true
                });
                
                var columnDefs = this.completeColumnDefs();
                var data = this.createDialog(columnDefs, this.language.edit.title, this.language.edit.button,
                    this.language.modalClose, 'editRowBtn', 'altEditor-edit-form');

                var selector = this.modal_selector;
                
                for (var j in columnDefs) {
                    var arrIndex = "['" + columnDefs[j].name.toString().split(".").join("']['") + "']";
                    var selectedValue = eval("adata.data()[0]" + arrIndex);
                    var jquerySelector = "#" + columnDefs[j].name.toString().replace(/\./g, "\\.");
                    $(selector).find(jquerySelector).val(this._quoteattr(selectedValue));
                    $(selector).find(jquerySelector).trigger("change"); // required by select2
                }
                
                $(selector + ' input[0]').focus();
                $(selector).trigger("alteditor:some_dialog_opened").trigger("alteditor:edit_dialog_opened");
            },

            /**
             * Callback for "Edit" button
             */
            _editRowData: function () {
                var that = this;
                var dt = this.s.dt;

                // Complete new row data
                var rowDataArray = {};

                var adata = dt.rows({
                    selected: true
                });

                // Getting the inputs from the edit-modal
                $(`form[name="altEditor-edit-form-${this.random_id}"] *`).filter(':input').each(function (i) {
                    rowDataArray[$(this).attr('id')] = $(this).val();
                });
		    
		//Getting the textArea from the modal
                $(`form[name="altEditor-add-form-${this.random_id}"] *`).filter('textarea').each(function (i) {
                    rowDataArray[$(this).attr('id')] = $(this).val();
                });

                console.log(rowDataArray); //DEBUG

                that.onEditRow(that,
                    rowDataArray,
                    function(data,b,c,d,e){ that._editRowCallback(data,b,c,d,e); },
                    function(data){ that._errorCallback(data);
                });
            },

            /**
             * Open Delete Modal for selected row
             *
             * @private
             */
            _openDeleteModal: function () {
                
                var that = this;
                var dt = this.s.dt;
                var adata = dt.rows({
                    selected: true
                });
                var columnDefs = this.completeColumnDefs();
                const formName = 'altEditor-delete-form-' + this.random_id;

                // TODO
                // we should use createDialog()
                // var data = this.createDialog(columnDefs, this.language.delete.title, this.language.delete.button,
                //      this.language.modalClose, 'deleteRowBtn', 'altEditor-delete-form');
                
                // Building delete-modal
                var data = "";

                for (var j in columnDefs) {
                    if (columnDefs[j].type.indexOf("hidden") >= 0) {
                        data += "<input type='hidden' id='" + columnDefs[j].title + "' value='" + adata.data()[0][columnDefs[j].name] + "'></input>";
                    }
                    else {
                        data += "<div style='margin-left: initial;margin-right: initial;' class='form-group row'><label for='"
                            + that._quoteattr(columnDefs[j].name)
                            + "'>"
                            + columnDefs[j].title
                            + ":&nbsp</label> <input  type='hidden'  id='"
                            + that._quoteattr(columnDefs[j].title)
                            + "' name='"
                            + that._quoteattr(columnDefs[j].title)
                            + "' placeholder='"
                            + that._quoteattr(columnDefs[j].title)
                            + "' style='overflow:hidden'  class='form-control' value='"
                            + that._quoteattr(adata.data()[0][columnDefs[j].name]) + "' >"
                            + adata.data()[0][columnDefs[j].name]
                            + "</input></div>";
                    }
                }

                var selector = this.modal_selector;
                $(selector).on('show.bs.modal', function () {
                    var btns = '<button type="button" data-content="remove" class="btn btn-default" data-dismiss="modal">' + that.language.modalClose + '</button>' +
                        '<button type="submit"  data-content="remove" class="btn btn-danger" id="deleteRowBtn">' + that.language.delete.button + '</button>';
                    $(selector).find('.modal-title').html(that.language.delete.title);
                    $(selector).find('.modal-body').html(data);
                    $(selector).find('.modal-footer').html(btns);
                    const modalContent = $(selector).find('.modal-content');
                    if (modalContent.parent().is('form')) {
                        modalContent.parent().attr('name', formName);
                        modalContent.parent().attr('id', formName);
                    } else {
                        modalContent.wrap("<form name='" + formName + "' id='" + formName + "' role='form'></form>");
                    }
                });

                $(selector).modal('show');
                $(selector + ' input[0]').focus();
                $(selector).trigger("alteditor:some_dialog_opened").trigger("alteditor:delete_dialog_opened");
            },

            /**
             * Callback for "Delete" button
             */
            _deleteRow: function () {
                var that = this;
                var dt = this.s.dt;

                var jsonDataArray = {};

                var adata = dt.rows({
                    selected: true
                });

                // Getting the IDs and Values of the tablerow
                for (var i = 0; i < dt.context[0].aoColumns.length; i++) {
                    // .data is the attribute name, if any; .idx is the column index, so it should always exists 
                    var name = dt.context[0].aoColumns[i].data ? dt.context[0].aoColumns[i].data :
                            dt.context[0].aoColumns[i].mData ? dt.context[0].aoColumns[i].mData :
                            dt.context[0].aoColumns[i].idx;
                    jsonDataArray[name] = adata.data()[0][name];
                }
                that.onDeleteRow(that,
                    jsonDataArray,
                    function(data){ that._deleteRowCallback(data); },
                    function(data){ that._errorCallback(data);
                });
            },

            /**
             * Open Add Modal for selected row
             *
             * @private
             */
            _openAddModal: function () {
                var dt = this.s.dt;
                var columnDefs = this.completeColumnDefs();
                var data = this.createDialog(columnDefs, this.language.add.title, this.language.add.button,
                    this.language.modalClose, 'addRowBtn', 'altEditor-add-form');

                var selector = this.modal_selector;
                $(selector + ' input[0]').focus();
                $(selector).trigger("alteditor:some_dialog_opened").trigger("alteditor:add_dialog_opened");
            },
            
            /**
            * Complete DataTable.context[0].aoColumns with default values
            */
            completeColumnDefs: function () {
                var columnDefs = [];
                var dt = this.s.dt;
                for (var i in dt.context[0].aoColumns) {
                    var obj = dt.context[0].aoColumns[i];
                    columnDefs[i] = {
                        title: obj.sTitle,
                        name: (obj.data ? obj.data : obj.mData),
                        type: (obj.type ? obj.type : 'text'),
			rows: (obj.rows ? obj.rows : '5'),
                        cols: (obj.cols ? obj.cols : '30'),
                        options: (obj.options ? obj.options : []),
                        readonly: (obj.readonly ? obj.readonly : false),
                        disabled: (obj.disabled ? obj.disabled : false),
                        required: (obj.required ? obj.required : false),
                        msg: (obj.errorMsg ? obj.errorMsg : ''),        // FIXME no more used
                        hoverMsg: (obj.hoverMsg ? obj.hoverMsg : ''),
                        pattern: (obj.pattern ? obj.pattern : '.*'),
                        special: (obj.special ? obj.special : ''),
                        unique: (obj.unique ? obj.unique : false),
                        uniqueMsg: (obj.uniqueMsg ? obj.uniqueMsg : ''),        // FIXME no more used
                        maxLength: (obj.maxLength ? obj.maxLength : false),
                        multiple: (obj.multiple ? obj.multiple : false),
                        select2: (obj.select2 ? obj.select2 : false),
                        datepicker: (obj.datepicker ? obj.datepicker : false),
                        datetimepicker: (obj.datetimepicker ? obj.datetimepicker : false),
                        editorOnChange: (obj.editorOnChange ? obj.editorOnChange : null)
                    }
                }
                return columnDefs;
            },
            
            /**
            * Create both Edit and Add dialogs
            * @param columnDefs as returned by completeColumnDefs()
            */
            createDialog: function(columnDefs, title, buttonCaption, closeCaption, buttonClass, formName) {
                formName = [formName, this.random_id].join('-');
                var data = "";
                for (var j in columnDefs) {
                    
                    //handle hidden fields
                    if (columnDefs[j].type.indexOf("hidden") >= 0) {
                        data += "<input type='hidden' id='" + columnDefs[j].name + "' ></input>";
                    }
                    else {
                        // handle fields that are visible to the user
                        data += "<div style='margin-left: initial;margin-right: initial;' class='form-group row' id='alteditor-row-" + this._quoteattr(columnDefs[j].name) +"'>";
                        data += "<div class='col-sm-3 col-md-3 col-lg-3 text-right' style='padding-top:4px;'>";
                        data += "<label for='" + columnDefs[j].name + "'>" + columnDefs[j].title + ":</label></div>";
                        data += "<div class='col-sm-8 col-md-8 col-lg-8'>";

                        // Adding readonly-fields
                        if (columnDefs[j].type.indexOf("readonly") >= 0) {
                            // type=readonly is deprecated, kept for backward compatibility
                            data += "<input type='text' readonly  id='"
                                + this._quoteattr(columnDefs[j].name)
                                + "' name='"
                                + this._quoteattr(columnDefs[j].title)
                                + "' placeholder='"
                                + this._quoteattr(columnDefs[j].title)
                                + "' style='overflow:hidden'  class='form-control  form-control-sm' value=''>";
                        }
                        // Adding select-fields
                        else if (columnDefs[j].type.indexOf("select") >= 0) {
                            var options = "";
                            var optionsArray = columnDefs[j].options;
                            if (optionsArray.length > 0) {
                                // array-style select or select2
                                for (var i = 0; i < optionsArray.length; i++) {
                                    options += "<option value='" + this._quoteattr(optionsArray[i])
                                        + "'>" + optionsArray[i] + "</option>";
                                }
                            } else {
                                // object-style select or select2
                                for (var x in optionsArray) {
                                    options += "<option value='" + this._quoteattr(x) + "' >"
                                        + optionsArray[x] + "</option>";
                                }
                            }
                            data += "<select class='form-control" + (columnDefs[j].select2 ? ' select2' : '')
                                + "' id='" + this._quoteattr(columnDefs[j].name)
                                + "' name='" + this._quoteattr(columnDefs[j].title) + "' "
                                + (columnDefs[j].multiple ? ' multiple ' : '')
                                + (columnDefs[j].readonly ? ' readonly ' : '')
                                + (columnDefs[j].disabled ? ' disabled ' : '')
                                + (columnDefs[j].required ? ' required ' : '')
                                + ">" + options
                                + "</select>";
                        }
			//Adding Text Area 
                        else if (columnDefs[j].type.indexOf("textarea") >= 0)
                        {
                            data += "<textarea id='" + this._quoteattr(columnDefs[j].name)
				+ "' name='" + this._quoteattr(columnDefs[j].title)
				+ "'rows='" + this._quoteattr(columnDefs[j].rows)
				+ "' cols='"+ this._quoteattr(columnDefs[j].cols)
				+ "'>"
				+ "</textarea>";
                        }
                        // Adding text-inputs and errorlabels, but also new HTML5 typees (email, color, ...)
                        else {
                            data += "<input type='" + this._quoteattr(columnDefs[j].type)
                                + "' id='" + this._quoteattr(columnDefs[j].name)
                                + "' pattern='" + this._quoteattr(columnDefs[j].pattern)
                                + "' title='" + this._quoteattr(columnDefs[j].hoverMsg)
                                + "' name='" + this._quoteattr(columnDefs[j].title)
                                + "' placeholder='" + this._quoteattr(columnDefs[j].title)
                                + "' data-special='" + this._quoteattr(columnDefs[j].special)
                                + "' data-errorMsg='" + this._quoteattr(columnDefs[j].msg)
                                + "' data-uniqueMsg='" + this._quoteattr(columnDefs[j].uniqueMsg)
                                + "' data-unique='" + columnDefs[j].unique
                                + "' "
                                + (columnDefs[j].readonly ? ' readonly ' : '')
                                + (columnDefs[j].disabled ? ' disabled ' : '')
                                + (columnDefs[j].required ? ' required ' : '')
                                + (columnDefs[j].maxLength == false ? "" : " maxlength='" + columnDefs[j].maxLength + "'")
                                + " style='overflow:hidden'  class='form-control  form-control-sm' value=''>";
                        }
                        data += "<label id='" + this._quoteattr(columnDefs[j].name) + "label"
                                + "' class='errorLabel'></label>";
                        data += "</div><div style='clear:both;'></div></div>";
                    }
                }
                // data += "</form>";
                
                var selector = this.modal_selector;
                $(selector).on('show.bs.modal', function () {
                    var btns = '<button type="button" data-content="remove" class="btn btn-default" data-dismiss="modal">'+closeCaption+'</button>' +
                        '<button type="submit" form="' + formName + '" data-content="remove" class="btn btn-primary" id="'+buttonClass+'">'+buttonCaption+'</button>';
                    $(selector).find('.modal-title').html(title);
                    $(selector).find('.modal-body').html(data);
                    $(selector).find('.modal-footer').html(btns);
                    const modalContent = $(selector).find('.modal-content');
                    if (modalContent.parent().is('form')) {
                        modalContent.parent().attr('name', formName);
                        modalContent.parent().attr('id', formName);
                    } else {
                        modalContent.wrap("<form name='" + formName + "' id='" + formName + "' role='form'></form>");
                    }
                });

                $(selector).modal('show');
                $(selector + ' input[0]').focus();
                
                var that = this;

                // enable select 2 items, datepicker, datetimepickerm
                for (var j in columnDefs) {
                    if (columnDefs[j].select2) {
                        // Require select2 plugin
                        $(selector).find("select#" + columnDefs[j].name).select2(columnDefs[j].select2);
                    } else if (columnDefs[j].datepicker) {
                        // Require jquery-ui
                        $(selector).find("#" + columnDefs[j].name).datepicker(columnDefs[j].datepicker);
                    } else if (columnDefs[j].datetimepicker) {
                        // Require datetimepicker plugin
                        $(selector).find("#" + columnDefs[j].name).datetimepicker(columnDefs[j].datetimepicker);
                    }
                    // custom onchange triggers
                    if (columnDefs[j].editorOnChange) {
                        var f = columnDefs[j].editorOnChange; // FIXME what if more than 1 editorOnChange ?
                        $(selector).find("#" + columnDefs[j].name).on('change', function(elm) {
                            f(elm, that);
                        });
                    }
                }
            },
            
            /**
             * Callback for "Add" button
             */
            _addRowData: function () {
                var that = this;
                var dt = this.s.dt;

                var rowDataArray = {};

                // Getting the inputs from the modal
                $(`form[name="altEditor-add-form-${this.random_id}"] *`).filter(':input').each(function (i) {
                    rowDataArray[$(this).attr('id')] = $(this).val();
                });
		    
		//Getting the textArea from the modal
                $(`form[name="altEditor-add-form-${this.random_id}"] *`).filter('textarea').each(function (i) {
                    rowDataArray[$(this).attr('id')] = $(this).val();
                });

//console.log(rowDataArray); //DEBUG

                that.onAddRow(that,
                    rowDataArray,
                    function(data){ that._addRowCallback(data); },
                    function(data){ that._errorCallback(data);
                });

            },

            /**
             * Called after a row has been deleted on server
             */
            _deleteRowCallback: function (response, status, more) {
                    var selector = this.modal_selector;
                    $(selector + ' .modal-body .alert').remove();

                    var message = '<div class="alert alert-success" role="alert">' +
                        '<strong>' + this.language.success + '</strong>' +
                        '</div>';
                    $(selector + ' .modal-body').append(message);

                    this.s.dt.row({
                        selected : true
                    }).remove();
                    this.s.dt.draw('page');

                    // Disabling submit button
                    $("div"+selector).find("button#addRowBtn").prop('disabled', true);
                    $("div"+selector).find("button#editRowBtn").prop('disabled', true);
                    $("div"+selector).find("button#deleteRowBtn").prop('disabled', true);
            },

            /**
             * Called after a row has been inserted on server
             */
            _addRowCallback: function (response, status, more) {
                
                    //TODO should honor dt.ajax().dataSrc
                    
                    var data = (typeof response === "string") ? JSON.parse(response) : response;
                    var selector = this.modal_selector;
                    $(selector + ' .modal-body .alert').remove();

                    var message = '<div class="alert alert-success" role="alert">' +
                        '<strong>' + this.language.success + '</strong>' +
                        '</div>';
                    $(selector + ' .modal-body').append(message);

                    this.s.dt.row.add(data).draw(false);

                    // Disabling submit button
                    $("div" + selector).find("button#addRowBtn").prop('disabled', true);
                    $("div" + selector).find("button#editRowBtn").prop('disabled', true);
                    $("div" + selector).find("button#deleteRowBtn").prop('disabled', true);
            },

            /**
             * Called after a row has been updated on server
             */
            _editRowCallback: function (response, status, more) {

                    //TODO should honor dt.ajax().dataSrc
                    
                    var data = (typeof response === "string") ? JSON.parse(response) : response;
                    var selector = this.modal_selector;
                    $(selector + ' .modal-body .alert').remove();

                    var message = '<div class="alert alert-success" role="alert">' +
                        '<strong>' + this.language.success + '</strong>' +
                        '</div>';
                    $(selector + ' .modal-body').append(message);

                    this.s.dt.row({
                        selected : true
                    }).data(data);
                    this.s.dt.draw('page');

                    // Disabling submit button
                    $("div" + selector).find("button#addRowBtn").prop('disabled', true);
                    $("div" + selector).find("button#editRowBtn").prop('disabled', true);
                    $("div" + selector).find("button#deleteRowBtn").prop('disabled', true);
            },

            /**
             * Called after AJAX server returned an error
             */
            _errorCallback: function (response, status, more) {
                    var error = response;
                    var selector = this.modal_selector;
                    $(selector + ' .modal-body .alert').remove();
                    var errstr = this.language.error.message;
                    if (error.responseJSON && error.responseJSON.errors) {
                        errstr = "";
                        for (var key in error.responseJSON.errors) {
                            errstr += error.responseJSON.errors[key][0];
                        }
                    }
                    var message = '<div class="alert alert-danger" role="alert">' +
                        '<strong>' + this.language.error.label + '</strong> ' + (error.status == null ? "" : this.language.error.responseCode + error.status) + " " + errstr +
                        '</div>';

                    $(selector + ' .modal-body').append(message);
            },
            
            /**
             * Default callback for insertion: mock webservice, always success.
             */
            onAddRow: function(dt, rowdata, success, error) {
                console.log("Missing AJAX configuration for INSERT");
                success(rowdata);
            },

            /**
             * Default callback for editing: mock webservice, always success.
             */
            onEditRow: function(dt, rowdata, success, error) {
                console.log("Missing AJAX configuration for UPDATE");
                success(rowdata);
            },

            /**
             * Default callback for deletion: mock webservice, always success.
             */
            onDeleteRow: function(dt, rowdata, success, error) {
                console.log("Missing AJAX configuration for DELETE");
                success(rowdata);
            },
            
            /**
             * Dinamically reload options in SELECT menu
            */
            reloadOptions: function($select, options) {
                var oldValue = $select.val();
                $select.empty(); // remove old options
                if (options.length > 0) {
                    // array-style select or select2
                    $.each(options, function(key, value) {
                      $select.append($("<option></option>")
                         .attr("value", value).text(value));
                    });
                } else {
                    // object-style select or select2
                    $.each(options, function(key, value) {
                      $select.append($("<option></option>")
                         .attr("value", value).text(key));
                    });
                }
                $select.val(oldValue); // if still present, of course
                $select.trigger('change');
            },

            /**
             * Sanitizes input for use in HTML
             * @param s
             * @param preserveCR
             * @returns {string}
             * @private
             */
            _quoteattr: function (s, preserveCR) {
                if (s == null)
                    return "";
                preserveCR = preserveCR ? '&#13;' : '\n';
                if (Array.isArray(s)) {
                    // for MULTIPLE SELECT
                    var newArray = [];
		    var x;
                    for (x in s) newArray.push(s[x]);
                    return newArray;
                }
                return ('' + s) /* Forces the conversion to string. */
                    .replace(/&/g, '&amp;') /* This MUST be the 1st replacement. */
                    .replace(/'/g, '&apos;') /* The 4 other predefined entities, required. */
                    .replace(/"/g, '&quot;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/\r\n/g, preserveCR) /* Must be before the next replacement. */
                    .replace(/[\r\n]/g, preserveCR);
            },
        });

    /**
     * altEditor version
     *
     * @static
     * @type String
     */
    altEditor.version = '2.0';

    /**
     * altEditor defaults
     *
     * @namespace
     */
    altEditor.defaults = {
        /**
         * @type {Boolean} Ask user what they want to do, even for a single
         *       option
         */
        alwaysAsk: false,

        /** @type {string|null} What will trigger a focus */
        focus: null, // focus, click, hover

        /** @type {column-selector} Columns to provide auto fill for */
        columns: '', // all

        /** @type {boolean|null} Update the cells after a drag */
        update: null, // false is editor given, true otherwise

        /** @type {DataTable.Editor} Editor instance for automatic submission */
        editor: null
    };

    /**
     * Classes used by altEditor that are configurable
     *
     * @namespace
     */
    altEditor.classes = {
        /** @type {String} Class used by the selection button */
        btn: 'btn'
    };

    // Attach a listener to the document which listens for DataTables
    // initialisation
    // events so we can automatically initialise
    $(document).on('preInit.dt.altEditor', function (e, settings, json) {
        if (e.namespace !== 'dt') {
            return;
        }

        var init = settings.oInit.altEditor;
        var defaults = DataTable.defaults.altEditor;

        if (init || defaults) {
            var opts = $.extend({}, init, defaults);

            if (init !== false) {

                var editor = new altEditor(settings, opts);
                // e is a jQuery event object
                // e.target is the underlying jQuery object, e.g. $('#mytable')
                // so that you can retrieve the altEditor object later
                e.target.altEditor = editor;
            }
        }
    });

    // Alias for access
    DataTable.altEditor = altEditor;
    return altEditor;
});
