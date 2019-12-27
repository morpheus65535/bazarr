/*
 * jQuery idleTimer plugin
 * version 0.8.092209
 * by Paul Irish. 
 *   http://github.com/paulirish/yui-misc/tree/
 * MIT license
 
 * adapted from YUI idle timer by nzakas:
 *   http://github.com/nzakas/yui-misc/
 
 
 * Copyright (c) 2009 Nicholas C. Zakas
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

(function($){

$.idleTimer = function f(newTimeout){

    //$.idleTimer.tId = -1     //timeout ID

    var idle    = false,        //indicates if the user is idle
        enabled = true,        //indicates if the idle timer is enabled
        timeout = 30000,        //the amount of time (ms) before the user is considered idle
        events  = 'mousemove keydown DOMMouseScroll mousewheel mousedown', // activity is one of these events
      //f.olddate = undefined, // olddate used for getElapsedTime. stored on the function
        
    /* (intentionally not documented)
     * Toggles the idle state and fires an appropriate event.
     * @return {void}
     */
    toggleIdleState = function(){
    
        //toggle the state
        idle = !idle;
        
        // reset timeout counter
        f.olddate = +new Date;
        
        //fire appropriate event
        $(document).trigger(  $.data(document,'idleTimer', idle ? "idle" : "active" )  + '.idleTimer');            
    },

    /**
     * Stops the idle timer. This removes appropriate event handlers
     * and cancels any pending timeouts.
     * @return {void}
     * @method stop
     * @static
     */         
    stop = function(){
    
        //set to disabled
        enabled = false;
        
        //clear any pending timeouts
        clearTimeout($.idleTimer.tId);
        
        //detach the event handlers
        $(document).unbind('.idleTimer');
    },
    
    
    /* (intentionally not documented)
     * Handles a user event indicating that the user isn't idle.
     * @param {Event} event A DOM2-normalized event object.
     * @return {void}
     */
    handleUserEvent = function(){
    
        //clear any existing timeout
        clearTimeout($.idleTimer.tId);
        
        
        
        //if the idle timer is enabled
        if (enabled){
        
          
            //if it's idle, that means the user is no longer idle
            if (idle){
                toggleIdleState();           
            } 
        
            //set a new timeout
            $.idleTimer.tId = setTimeout(toggleIdleState, timeout);
            
        }    
     };
    
      
    /**
     * Starts the idle timer. This adds appropriate event handlers
     * and starts the first timeout.
     * @param {int} newTimeout (Optional) A new value for the timeout period in ms.
     * @return {void}
     * @method $.idleTimer
     * @static
     */ 
    
    
    f.olddate = f.olddate || +new Date;
    
    //assign a new timeout if necessary
    if (typeof newTimeout == "number"){
        timeout = newTimeout;
    } else if (newTimeout === 'destroy') {
        stop();
        return this;  
    } else if (newTimeout === 'getElapsedTime'){
        return (+new Date) - f.olddate;
    }
    
    //assign appropriate event handlers
    $(document).bind($.trim((events+' ').split(' ').join('.idleTimer ')),handleUserEvent);
    
    
    //set a timeout to toggle state
    $.idleTimer.tId = setTimeout(toggleIdleState, timeout);
    
    // assume the user is active for the first x seconds.
    $.data(document,'idleTimer',"active");
      
    

    
}; // end of $.idleTimer()

    

})(jQuery);
