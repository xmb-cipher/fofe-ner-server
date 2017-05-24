<?php
// phpinfo();
if( $_POST['lang']) {

        $lang = $_POST['lang'];

        // English
        $url = 'video.eecs.yorku.ca:20540';

        if ($lang == "Spanish"){
                $url = 'video.eecs.yorku.ca:20541';
        } elseif ($lang == "Chinese"){
                $url = 'video.eecs.yorku.ca:20542';
        }

        $fields = array(
                'mode' => $_POST['mode'],
                'text' => $_POST['text'],
                'lang' => $_POST['lang']
        );

	// build the urlencoded data
        $postvars = http_build_query($fields);

        // open connection
        $ch = curl_init();

        // set the url, number of POST vars, POST data
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_POST, count($fields));
        curl_setopt($ch, CURLOPT_POSTFIELDS, $postvars);

        // execute post
        $result = curl_exec($ch);

        // close connection
        curl_close($ch);
}
?>