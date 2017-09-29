
var schema = {
    entity_types: [
        // CoNLL2003
        {
            type   : 'PER',
            labels : ['PERSON'],
            bgColor: '#FFCCAA',
            borderColor: 'darken'   },
        {
            type   : 'ORG',
            labels : ['ORGANIZATION'],
            bgColor: '#8FB2FF',
            borderColor: 'darken'   },
        {
            type   : 'LOC',
            labels : ['LOCATION'],
            bgColor: '#95DFFF',
            borderColor: 'darken'   },
        {
            type   : 'MISC',
            labels : ['MISCELLANEOUS'],
            bgColor: '#F1F447',
            borderColor: 'darken'   },

        // KBP2016
        { type   : 'PER_NAM',
            labels : ['PER-NAME'],
            bgColor: '#FFCCAA',
            borderColor: 'darken'},
        { type   : 'ORG_NAM',
            labels : ['ORG-NAME'],
            bgColor: '#8FB2FF',
            borderColor: 'darken'},
        { type   : 'GPE_NAM',
            labels : ['GPE-NAME'],
            bgColor: '#8be0b2',
            borderColor: 'darken'},
        { type   : 'LOC_NAM',
            labels : ['LOC-NAME'],
            bgColor: '#95DFFF',
            borderColor: 'darken'},
        { type   : 'FAC_NAM',
            labels : ['FAC-NAME'],
            bgColor: '#948be0',
            borderColor: 'darken'},
        { type   : 'PER_NOM',
            labels : ['PER-NOMINAL'],
            bgColor: '#e0ad8b',
            borderColor: 'darken'},
        { type   : 'ORG_NOM',
            labels : ['ORG-NOMINAL'],
            bgColor: '#FF6A32',
            borderColor: 'darken'},
        { type   : 'GPE_NOM',
            labels : ['GPE-NOMINAL'],
            bgColor: '#38c177',
            borderColor: 'darken'},
        { type   : 'LOC_NOM',
            labels : ['LOC-NOMINAL'],
            bgColor: '#6eafcc',
            borderColor: 'darken'},
        { type   : 'FAC_NOM',
            labels : ['FAC-NOMINAL'],
            bgColor: '#645baf',
            borderColor: 'darken'}
    ]
};

var glob_response = null;

var demo_success_handler = function(response) {
    // pass language detection
    var notes = response.notes;
    var $errors, $el;
    var $linking = $('#linking');

    // ERROR: Language not supported - if the user enters a text in a language other than English, Spanish or Chinese
    if (notes.localeCompare("Language not supported.") == 0){
        $errors = $('#errors');
        $el = '<div class="error-banner"><h4>' + notes + '</h4></div>';
        $errors.append($el);
        $("#spinner").css("display", "none");

        // Language is supported
    } else {

        // If there are still some other error messages - display
        if (notes.length != 0){
            $errors = $('#errors');
            $el = '<div class="success-banner"><h4>' + notes + '</h4></div>';
            $errors.append($el);
        }

        $linking.html('');
        $('#analysis').html('<div id="fofe-ner-out"></div>');

        // Brat visualizations
        var dispatcher = Util.embed('fofe-ner-out', schema, response, webFontURLs);

        // Error checking
        if ((typeof response) === 'string'){
            response = JSON.parse(response);
        }
        glob_response = response;

        // Remove the spinner and display the linking info
        var loadDone = function() {
            $("#spinner").css("display", "none");
            $linking.css("display", "block");

            var end = new Date().getTime();
            var time = end - start;
            console.log('Execution time: ' + time);
        };

        // When brat visualization done loading
        dispatcher.on("doneRendering", loadDone);

        // Info thumbnail: display full mention, MID, candidate MIDs, Summary, Confidence
        var info_thumbnail = function() {
            $linking.html('');
            var text = glob_response.text, entities = glob_response.entities;
            var mids = glob_response.mids;
            var mention = arguments[5];
            var mid = arguments[7];
            var summary = arguments[6];

            var full_mention, candidate_list, $candidate_string, freebase, $element;

            // If candidate MIDs are available in the response
            if (Object.keys(mids).length != 0) {
                mid = mids[mention][0];
                full_mention = mids[mention][1];
                candidate_list = mids[mention][2];
                $candidate_string = '<p class="mid"><strong class="bolden">Candidates: </strong><span class="more-mids">';
                if (candidate_list.length != 0){
                    for (i = 0; i < candidate_list.length; i++){
                        $element = "<a href='http://www.eecs.yorku.ca/~watchara/cgi/FBFL2054_QUERY.cgi?Search_Input="
                            + candidate_list[i]+"&Input_Type=ANY&Input_Language=en&Result_Type=ALL&Resu" +
                            "lt_Limit=UNLIMITED' target='_blank' >" + candidate_list[i] + ", </a>";
                        $candidate_string += $element;
                    }
                }
                //$candidate_string = $candidate_string.slice(0, -5); // # remove last comma
                $candidate_string += '</a></span></p>';

                if (candidate_list.length == 0)
                    $candidate_string = '<p class="mid"><strong class="bolden">Candidates: </strong>None</p>';

                summary = mids[mention][3];

                freebase = "<a href='http://www.eecs.yorku.ca/~watchara/cgi/FBFL2054_QUERY.cgi?Search_Input="+ mid
                    +"&Input_Type=ANY&Input_Language=en&Result_Type=ALL&Result_Limit=UNLIMITED' target='_blank'>";

                if (mid.localeCompare("Unknown") == 0)
                    freebase = "";

                // Candidate MIDs are not available in the response
            } else {
                mid = "Unknown";
                full_mention = mention;
                $candidate_string = '<p class="mid"><strong class="bolden">Candidates: </strong>None</p>';
                summary = "N/A";
                freebase = "";
            }

            var i, s, m, id, ent_type = null, score = null;
            for (i = 0; i < entities.length; i++) {
                s = entities[i][2][0]; // slice array
                m = text.slice(s[0], s[1]);

                if (m.localeCompare(mention) == 0){
                    ent_type = entities[i][1];
                    score = entities[i][3];
                    id = entities[i][0];
                }
            }

            console.log(ent_type);
            // add card to the linking
            var icon = '<div class="icon per-icon"><i class="fa fa-user fa-5x icon" aria-hidden="true"></i></div>';
            var type = "PER-NAME";
            if ((ent_type.localeCompare("ORG") === 0) || (ent_type.localeCompare("ORG_NAM") == 0)){
                icon = '<div class="icon org-icon"><i class="fa fa-university fa-5x icon" aria-hidden="true"></i></div>';
                type = "ORG-NAME";
            }
            else if ((ent_type.localeCompare("LOC") == 0) || (ent_type.localeCompare("LOC_NAM") == 0)){
                icon = '<div class="icon loc-icon"><i class="fa fa-map-marker fa-5x icon" aria-hidden="true"></i></div>';
                type = "LOC-NAME";
            }
            else if (ent_type.localeCompare("MISC") == 0) {
                icon = '<div class="icon misc-icon"><i class="fa  fa-object-group fa-5x icon" aria-hidden="true"></i></div>';
                type = "MISC";
            }

            else if (ent_type.localeCompare("GPE_NAM") == 0){
                icon = '<div class="icon gpe-icon"><i class="fa  fa-globe fa-5x icon" aria-hidden="true"></i></div>';
                type = "GPE-NAME";
            }

            else if (ent_type.localeCompare("FAC_NAM") == 0){
                icon = '<div class="icon fac-icon"><i class="fa fa-building-o fa-5x icon" aria-hidden="true"></i></div>';
                type = "FAC-NAME";
            }

            else if (ent_type.localeCompare("GPE_NOM") == 0){
                icon = '<div class="icon gpenom-icon"><i class="fa  fa-globe fa-5x icon" aria-hidden="true"></i></div>';
                type = "GPE-NOMINAL";
            }

            else if (ent_type.localeCompare("FAC_NOM") == 0){
                icon = '<div class="icon facnom-icon"><i class="fa fa-building-o fa-5x icon" aria-hidden="true"></i></div>';
                type = "FAC-NOMINAL";
            }
            else if (ent_type.localeCompare("PER_NOM") == 0){
                icon = '<div class="icon pernom-icon"><i class="fa fa-user fa-5x icon" aria-hidden="true"></i></div>';
                type = "PER-NOMINAL";
            }

            else if (ent_type.localeCompare("LOC_NOM") == 0){
                icon = '<div class="icon locnom-icon"><i class="fa fa-globe fa-5x icon" aria-hidden="true"></i></div>';
                type = "LOC-NOMINAL";
            }


            else if (ent_type.localeCompare("ORG_NOM") == 0){
                icon = '<div class="icon orgnom-icon"><i class="fa fa-university fa-5x icon" aria-hidden="true"></i></div>';
                type = "ORG-NOMINAL";
            }

            var myvar =
                '<div class="row">'+
                '    <div class="container thumbnail col-sm-12 col-md-8">'+
                '        <div class="col-sm-12 col-md-6 ' + id + '">'+
                '            <div class="icon-card">'+ icon + '<div class="ent_type"><h4>' + type + '</h4></div>' +
                ''+
                '            </div>'+
                '            <div class="info">'+
                '                <h4 class="card-title">'+ full_mention + '</h4>'+
                '                <p class="mid"><strong class="bolden">MID: </strong>' + freebase  +  mid + '</a></p>'+
                $candidate_string +
                '                <p class="mid"><strong class="bolden">Confidence: </strong>' + score +'</p>' +
                '            </div>'+
                '        </div>'+
                ''+
                '        <div class="col-sm-12 col-md-6">'+
                '            <div class="summary">'+
                '               <p class="card-text"><strong class="bolden">Summary: </strong><span class="more">' + summary + '</span></p>' +
                '            </div>'+
                '        </div>'+
                '    </div>'+
                '</div>';

            $('#linking').append(myvar);

            $('.thumbnail').css({'box-shadow': '0 1px 5px rgba(0, 0, 0, 0.15)'});

            $('.thumbnail').fadeIn({queue: false, duration: 'slow'});
            $('.thumbnail').animate({ top: "-10px" }, 'slow');

            // Show More/ Show less
            //**************************************************************************************************

            var showChar = 300;  // How many characters are shown by default
            var showMIDs = 5;
            var ellipsestext = "...";
            var moretext = "Show more >";
            var lesstext = "Show less";

            $('.more').each(function() {
                var content = $(this).html();

                if(content.length > showChar) {

                    var c = content.substr(0, showChar);
                    var h = content.substr(showChar, content.length - showChar);

                    var html = c + '<span class="moreellipses">' + ellipsestext+ '&nbsp;</span>' +
                        '<span class="morecontent"><span>' +
                        h + '</span>&nbsp;&nbsp;<a href="" class="morelink">' + moretext + '</a></span>';

                    $(this).html(html);
                }
            });

            var numMIDs = $(".more-mids a").length;
            console.log(numMIDs);

            if(numMIDs > showMIDs) {
                var beginning = "";
                var rest = "";
                i = 0;
                $(".more-mids a").each(function(){
                    if (i < 5)
                        beginning += $(this).prop('outerHTML');
                    else
                        rest += $(this).prop('outerHTML');
                    i++;
                });
                var html2 = beginning + '<span class="moreellipses">' + ellipsestext+ '&nbsp;</span>' +
                    '<span class="morecontent">' +
                    '<span>' + rest + '</span>&nbsp;&nbsp;<a href="" class="morelink">' + moretext + '</a></span>';
                $('.more-mids').html(html2);
            }

            $(".morelink").click(function(){
                if($(this).hasClass("less")) {
                    $(this).removeClass("less");
                    $(this).slideUp(500, function () {
                        $(this).html(moretext);
                        $(this).slideDown(500)
                    });
                } else {
                    $(this).addClass("less");
                    $(this).slideUp(500, function () {
                        $(this).html(lesstext);
                        $(this).slideDown(500)
                    });

                }
                $(this).parent().prev().slideToggle("slow");
                $(this).prev().slideToggle("slow");
                return false;
            });

            //**********************************************************************************************************

        };

        dispatcher.on('displaySpanComment', info_thumbnail);
    }
};

var main = function() {

    // Developer mode
    $('#dev_submit').click(function(){
        // Erase all of the analysis, error messages after each submit (since the text might be different)
        $('#analysis').html('');
        $('#errors').html('');
        $("#spinner").css("display", "block");
        $('#linking').css("display", "none");
        var userInput = $('#user-input').val();
        var selectedText = $("#lang-sel").find("option:selected").text();
        $.ajax({
            // url: 'info.php',
            url: '/',
            type: 'POST',
            data: {
                mode : 'dev',
                text : userInput,
                lang: selectedText
            },
            dataType: 'JSON',
            success: function(response){
                // TODO: show inference step by step
                console.log("response");
                console.log(response);

                $('#linking').html('');
                //$('#analysis').html('<div id="fofe-ner-out"></div>');

                var first_pass_shown = response.first_pass_shown;
                var first_pass_hidden = response.first_pass_hidden;
                var second_pass = response.second_pass;

                var container = '<div class="first_pass_space row"></div><div class="second_pass_space row"></div>';
                $('#analysis').append($(container));

                // First pass
                var num_sent = Object.keys(first_pass_shown).length;
                var j, dispatcher, element_div, ent_type, s, mention, score, entities, text, info;

                // $('#analysis').append('<div class="pull-left row "><h3> First pass: </h3></div>');
                for (j = 0; j < num_sent; j++){ // loop through sentences

                    element_div = '<div class="container" id="container-first_pass' + j + '"><div id="first_pass' + j
                        + '"></div><div class="row" id="info_first_pass' + j + '"></div></div>';
                    $('.first_pass_space').append(element_div);
                    dispatcher = Util.embed('first_pass' + j, schema, first_pass_shown[j], webFontURLs);

                    // first pass shown (outputted by model)
                    entities = first_pass_shown[j].entities;
                    text = first_pass_shown[j].text;
                    for (i = 0; i < entities.length; i++){ // loop through mentions
                        console.log("looping once");
                        ent_type = entities[i][1];
                        s = entities[i][2][0]; // slice array
                        mention = text.slice(s[0], s[1]);
                        score = entities[i][3];

                        info = '<div class="">' +
                            '<div class="info-background pull-left col-md-4">' +
                            '         <div class="info">'+
                            '                <h4 class="card-title">'+ mention + '</h4>'+
                            '                <p class="mid"><strong class="bolden">Confidence: </strong>' + score +'</p>' +
                            '         </div></div></div>';
                        $("#info_first_pass" + j).append(info);
                    }

                    // first pass hidden (ignored by model)
                    entities = first_pass_hidden[j].entities;
                    text = first_pass_hidden[j].text;
                    for (i = 0; i < entities.length; i++){ // loop through mentions
                        console.log("looping once");
                        ent_type = entities[i][1];
                        s = entities[i][2][0]; // slice array
                        mention = text.slice(s[0], s[1]);
                        score = entities[i][3];

                        info = '<div class="">' +
                            '<div class="info-background pull-left col-md-4">' +
                            '         <div class="info">'+
                            '                <h4 class="card-title color-pink" style="color:palevioletred;">'+ mention + '</h4>'+
                            '                <p class="mid"><strong class="bolden">Confidence: </strong>' + score +'</p>' +
                            '                <p class="entity-type"><strong class="bolden">Entity Type: </strong>' + ent_type +'</p>' +
                            '         </div></div></div>';
                        $("#info_first_pass" + j).append(info);
                    }
                }

                // Second pass
                if (second_pass.localeCompare("N/A") != 0) {
                    for (j = 0; j < num_sent; j++){ // loop through sentences
                        entities = second_pass[j].entities;
                        text = second_pass[j].text;

                        element_div = '<div class="container" id="container-second_pass' + j + '"><div id="second_pass'
                            + j + '"></div><div class="row" id="info_second_pass' + j + '"></div></div>';
                        $('.second_pass_space').append(element_div);
                        dispatcher = Util.embed('second_pass' + j, schema, second_pass[j], webFontURLs);

                        for (var i = 0; i < entities.length; i++){ // loop through mentions
                            console.log("looping once");
                            ent_type = entities[i][1];
                            s = entities[i][2][0]; // slice array
                            mention = text.slice(s[0], s[1]);
                            score = entities[i][3];

                            info = '<div class="">' +
                                '<div class="info-background pull-left col-md-4">' +
                                '         <div class="info">'+
                                '           <h4 class="card-title">'+ mention + '</h4>'+
                                '           <p class="mid"><strong class="bolden">Confidence: </strong>' + score +'</p>' +
                                '         </div></div></div>';
                            $("#info_second_pass" + j).append(info);
                        }
                    }
                }

                var loadDone = function() {
                    $("#spinner").css("display", "none");
                    $('#linking').css("display", "block");
                };

                dispatcher.on("doneRendering", loadDone);
            }
        });
    });

    // Demo mode
    $('#submit').click(function(){
        // Selected text
        var selectedText = $("#lang-sel").find("option:selected").text();
        var start = new Date().getTime();

        // Erase all of the analysis, error messages after each submit (since the text might be different)
        $('#analysis').html('');
        $('#errors').html('');
        $("#spinner").css("display", "block");
        $('#linking').css("display", "none");

        var userInput = $('#user-input').val();
        $.ajax({
            //url: 'info.php',
            url: '/',
            type: 'POST',
            data: {
                mode : 'demo',
                text : userInput,
                lang: selectedText
            },
            dataType: 'JSON',
            success: demo_success_handler,
            error: function(error) {
                console.log(error);
            }
        });
    });
};

head.ready(main);
