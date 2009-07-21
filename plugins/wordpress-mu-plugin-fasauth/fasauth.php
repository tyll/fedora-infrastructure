<?php
/*
Plugin Name: FAS Authentication
Plugin URL: http://fedoraproject.org
Description: FAS Authentication integration plugin
Version: 0.1.0
Author: Fedora Infrastructure Team
Author URI: http://fedoraproject.org/wiki/Infrastructure
*/

// let's disable a few things
add_action('lost_password', 'disable_function');
add_action('retrieve_password', 'disable_function');
add_action('password_reset', 'disable_function');


// overriding wp_authenticate
if(!function_exists('wp_authenticate')) :

function wp_authenticate($username, $password) {
	$username = sanitize_user($username);

	if ($username == '' || $password == '') {
		return new WP_Error('empty_username', __('<strong>ERROR</strong>: The username or password field is empty.'));
	}

	$ch = curl_init();
	curl_setopt($ch, CURLOPT_URL, 'http://publictest3.fedoraproject.org/accounts/json/person_by_username?tg_format=json');
	curl_setopt($ch, CURLOPT_POST, 1);
	curl_setopt($ch, CURLOPT_USERAGENT, "Auth_FAS 0.9");
	curl_setopt($ch, CURLOPT_POSTFIELDS, "username=".$username."&user_name=".$username."&password=".$password."&login=Login");                            
	curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
	curl_setopt($ch, CURLOPT_VERBOSE, 1);
	$fasuserdata = json_decode(curl_exec($ch), true);
	curl_close ($ch);

	// fas login successful
	if (isset($fasuserdata["success"]) && $fasuserdata['person']['status'] == 'active') {

		// check minimum group requirements
		if (check_grp_req($fasuserdata) !== true) {
			return new WP_Error('incorrect_password', __('<strong>Error</strong>: You do not meet minimum requirements to login.'));		
		}
		
		
		//echo "Min response: ".$min_req;

		// let's check wp db for user
		$user = get_userdatabylogin($username);

		// user not found, let's create db entry for it
		if ( !$user || ($user->user_login != $username) ) {			
			$user_id = create_wp_user($username);
			if (!$user_id) {
				return new WP_Error('incorrect_password', __('<strong>Error</strong>: Unable to create account. Please contact the webmaster.'));		
			}
			
			return new WP_User($user_id);
		}

		// all good, let go on
		return new WP_User($user->ID);
		
	} else {
		return new WP_Error('incorrect_password', __('<strong>Status</strong>: FAS Login NOT successful.'));
	}
}

// creates user in wp db
function create_wp_user($username) {
	$password = '';
	$email_domain = 'fedoraproject.org';

	require_once(WPINC . DIRECTORY_SEPARATOR . 'registration.php');
	return wpmu_create_user($username, $password, $username.'@'.$email_domain);
}

/*
* Used to disable certain login functions, e.g. retrieving a
* user's password.
*/
function disable_function() {
	die('Feature disabled.');
	//return new WP_Error('disabled_feature', __('<strong>ERROR</strong>: This feature is disabled.'));
}

/*
*  checks minimum group requirements
*/
function check_grp_req($user) {

	$groups = $user["person"]["approved_memberships"];

	//echo "Group: ". print_r($groups);
	
	// checking other group memberships
	$match = 0;
	$in_cla = false;
	for ($i = 0, $cnt = count($groups); $i < $cnt; $i++) {
		
		// user must be in cla
		if ($groups[$i]["name"] == "cla_done") {
			$in_cla = true;
		}

		// keep count of anything non-cla
		if (!preg_match('/^cla_/', $groups[$i]["name"])) {
			$match++;
		}
	}
	
	// yay, more than 1 non-cla group
	if ($match > 0 and $in_cla) {
		return true;
	}
	
	// if all else fails
	return false;

}

endif;

?>
