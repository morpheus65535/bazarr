/*
    jTable localization file for 'Hungarian' language.
    Author: Erik Berman
*/
(function ($) {

    $.extend(true, $.hik.jtable.prototype.options.messages, {
        serverCommunicationError: 'Adatbázis hiba',
        loadingMessage: 'Adatok betöltése...',
        noDataAvailable: 'Nincs elérhető adat!',
        addNewRecord: '+ Új hozzáadása',
        editRecord: 'Módosít',
        areYouSure: 'Biztos benne?',
        deleteConfirmation: 'Az adat véglegesen törlődik. Biztos benne?',
        save: 'Mentés',
        saving: 'Mentés',
        cancel: 'Mégse',
        deleteText: 'Töröl',
        deleting: 'Törlés',
        error: 'Hiba',
        close: 'Bezár',
        cannotLoadOptionsFor: '{0} mező opciói nem elérhetőek!',
        pagingInfo: 'Megjelenítve: {0} - {1} / Összesen: {2}',
        canNotDeletedRecords: '{1} tételből {0} nem törölhető!',
        deleteProggress: '{1} tételből {0} törölve, feldolgozás...',
        pageSizeChangeLabel: 'Row count', //New. Must be localized.
        gotoPageLabel: 'Go to page' //New. Must be localized.
});

})(jQuery);
