
var schema = {
    entity_types: [ 
        {
            type   : 'PER',
            labels : ['PER'],
            bgColor: '#FFCCAA',
            borderColor: 'darken'   },
        {
            type   : 'ORG',
            labels : ['ORG'],
            bgColor: '#8FB2FF',
            borderColor: 'darken'   },
        {
            type   : 'LOC',
            labels : ['LOC'],
            bgColor: '#95DFFF',
            borderColor: 'darken'   },
        {
            type   : 'MISC',
            labels : ['MISC'],
            bgColor: '#F1F447',
            borderColor: 'darken'   }, ]
};




// var docData = {
//     text     : "Ed O'Kelley was the man who shot the man who shot Jesse James.",
//     entities : [
//         ['T1', 'Person', [[0, 11]]],
//         ['T2', 'Person', [[20, 23]]],
//         ['T3', 'Person', [[37, 40]]],
//         ['T4', 'Person', [[50, 61]]],
//     ],
// };



head.ready(function() {
    // Util.embed('analysis', $.extend({}, collData),
    //         $.extend({}, docData), webFontURLs);
    $('#submit').click(function(){
        var userInput = $('#user-input').val();
        $.ajax({
            url: '/',
            type: 'POST',
            data: {
                mode : 'dev',
                text : userInput
            },
            dateType: 'JSON',
            success: function(response) {
                console.log(response);
                $('#analysis').html('<div id="fofe-ner-out"></div>')
                var dispatcher = Util.embed('fofe-ner-out', schema, response, webFontURLs);
                
                var showLinking = function() {
                    if ($('#linking-content').length == 0) {
                        var mention = arguments[5];
                        var e = arguments[0];
                        var obj = arguments[1];
                        var mid = arguments[7];
                        var summary = arguments[6];

                        $('#linking').html(
                            '<div id="linking-content">\n' + 
                                '<div>' + mention + '</div>' +
                                '<div>MID: Unknown</div>\n' +
                                '<hr>\n' + 
                                "<dir>Here's the summry of the mention</dir>\n" +
                            '</div>'
                        );

                        var posX = e.pageX;
                        var posY = e.pageY;
                        var offsetX = posX - 16;
                        if (offsetX + $('#linking').width() > $(window).width()) {
                            offsetX = $(window).width() - $('#linking').width() - 32;
                        }
                        var offsetY = posY - 16;
                        if (offsetY + $('#linking').height() > $(window).height()) {
                            offsetY = posY - $('#linking').height() + 32;
                        }

                        // TODO: sometimes beyong page
                        $('#linking').css({
                            'position': 'absolute', 
                            'top': offsetY, 
                            'left': offsetX
                        });
                        
                        $('#linking').mouseleave(function() {
                            $('#linking').html('');
                        });
                    }
                }
                dispatcher.on('displaySpanComment', showLinking);

                // var logArguments = function() { 
                //   console.log(arguments); 
                // } 
                // dispatcher.on('displaySpanComment', logArguments); 
                // dispatcher.on('displayArcComment', logArguments); 
                // dispatcher.on('displaySentComment', logArguments); 
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});