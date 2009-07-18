<?php
/*
Plugin Name: External DB authentication
Plugin URI: http://www.ploofle.com/tag/ext_db_auth/
Description: Used to externally authenticate WP users with an existing user DB.
Version: 3.1
Author: Charlene Barina
Author URI: http://www.ploofle.com

    Copyright 2007  Charlene Barina  (email : cbarina@u.washington.edu)

    This program is free software; you can redistribute it and/or modify
    it  under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
*/

//backwords compatability with php < 5 for htmlspecialchars_decode
if ( !function_exists('htmlspecialchars_decode') )
{
    function htmlspecialchars_decode($text)
    {
        return strtr($text, array_flip(get_html_translation_table(HTML_SPECIALCHARS)));
    }
}

function fas_auth_activate() {
	add_option('fas_url',"","FAS URL");
}

function fas_auth_init(){
	register_setting('ext_db_auth','fas_url');
 
}

//page for config menu
function fas_auth_add_menu() {
	add_options_page("External DB settings", "External DB settings", 10, __FILE__,"ext_db_auth_display_options");
}

function fas_auth_display_options() { 
    $db_types[] = "MySQL";
    $db_types[] = "MSSQL";
    $db_types[] = "PgSQL";
?>
	<div class="wrap">
	<h2>External database settings</h2>        
	<form method="post" action="options.php">
	<?php settings_fields('ext_db_auth'); ?>
        <h3>Connection settings</h3>
        <p>Caution: If you make a mistake, it will lock you out of your Wordpress installation, and you'll have to delete or rename the plugin file to regain access!</p>
		  <strong>Make sure your WP admin account exists in the external db prior to saving these settings.</strong>
        <table class="form-table">
        <tr>
            <th>External database type:</th>
                <td><select name="ext_db_type">
                <?php 
                    foreach ($db_types as $key=>$value) { //print out radio buttons
                        if ($value == get_option('ext_db_type'))
                            echo '<option value="'.$value.'" selected="selected">'.$value.'<br/>';
                        else echo '<option value="'.$value.'">'.$value.'<br/>';;
                    }                
                ?>
                </select>
                <br/><strong style="color:red;">required</strong>; If not MySQL, requires <a href="http://pear.php.net/package/MDB2/" target="_blank">PEAR MDB2 package</a> and relevant database driver package installation.
        </tr>        
        <tr>
            <th><label>Path to MDB2.php:</label></th><td><input type="text" name="ext_db_mdb2_path" value="<?php echo get_option('ext_db_mdb2_path'); ?>" /> <br/>
            In case this isn't in some sort of include path in your PHP configuration.  No trailing slash! e.g., /home/username/php <td>
        </tr>
        <tr>
            <th><label>External database host:</label></th><td><input type="text" name="ext_host" value="<?php echo get_option('ext_host'); ?>" /> <br/><strong style="color:red;">required</strong>; (often localhost) <td>
        </tr>
        <tr>
            <th><label>External database connection port:</label></th><td><input type="text" name="ext_db_port" value="<?php echo get_option('ext_db_port'); ?>" /> <br/>Only set this if you have a non-standard port for connecting.<td>
        </tr>        
        <tr>
            <th><label>External database name:</label></th><td><input type="text" name="ext_db" value="<?php echo get_option('ext_db'); ?>" /><br/><strong style="color:red;">required</strong><td>
        </tr>
        <tr>
            <th><label>External database username:</label></th><td><input type="text" name="ext_db_user" value="<?php echo get_option('ext_db_user'); ?>" /><br/><strong style="color:red;">required</strong>; (recommend select privileges only)<td>
        </tr>
        <tr>
            <th><label>External database password:</label></th><td><input type="password" name="ext_db_pw" value="<?php echo get_option('ext_db_pw'); ?>" /><br/><strong style="color:red;">required</strong><td>
        </tr>
        <tr>
            <th><label>Table containing users:</label></th><td><input type="text" name="ext_db_table" value="<?php echo get_option('ext_db_table'); ?>" /><br/><strong style="color:red;">required</strong><td>
        </tr>
        
        </table>
        
        <h3>Field matching settings</h3>
        <p>Username, password, and password hash type have to be set at the minimum. Be careful with this section! If you enter incorrect settings, you'll get locked out of your admin panel and will need to delete the plugin or change plugin settings directly in the wp_options table.</p>
        <table class="form-table">
        <tr>
            <th><label>Username field:</label></th><td><input type="text" name="ext_db_namefield" value="<?php echo get_option('ext_db_namefield'); ?>" /><br/><strong style="color:red;">required</strong><td>
        </tr>
        <tr>
            <th><label>User password field:</label></th><td><input type="text" name="ext_db_pwfield" value="<?php echo get_option('ext_db_pwfield'); ?>" /><br/><strong style="color:red;">required</strong><td>
        </tr>
        <tr>
            <th>Type of encryption for password:</th>
                <td><select name="ext_db_enc">
                <?php 
                    switch(get_option('ext_db_enc')) {
                    case "SHA1" :
                        echo '<option selected="selected">SHA1</option><option>MD5</option><option>Other</option>';
                        break;
                    case "MD5" :
                        echo '<option>SHA1</option><option selected="selected">MD5</option><option>Other</option>';
                        break;                
                    case "Other" :
                        echo '<option>SHA1</option><option  selected="selected">MD5</option><option selected="selected">Other</option>';
                        break;                                        
                    default :
                        echo '<option selected="selected">SHA1</option><option>MD5</option><option>Other</option>';
                        break;
                    }
                ?>
            </select><br/><strong style="color:red;">required</strong>; (using "Other" requires you to enter PHP code below!)</td>            
        </tr>
        <tr>
            <th><label>Other encryption:</label></th><td><input type="text" name="ext_db_other_enc" size="100" value="<?php echo get_option('ext_db_other_enc'); ?>" /><br/>Enter code here; only will run if "Other" is selected. Variable you need to set is $password2. See source code for other variable names.<td>
        </tr>
		  <tr>
            <th><label>Role field for validation:</label></th><td><input type="text" name="ext_db_role" value="<?php echo get_option('ext_db_role'); ?>" /> 
				<select name="ext_db_role_bool">
                <?php 
                    switch(get_option('ext_db_role_bool')) {
                    case "is" :
                        echo '<option selected="selected">is</option><option>greater than</option><option>less than</option>';
                        break;
                    case "greater than" :
                        echo '<option>is</option><option selected="selected">greater than</option><option>less than</option>';
                        break;                
                    case "less than" :
                        echo '<option>is</option><option>greater than</option><option selected="selected">less than</option>';
                        break;                                        
                    default :
                        echo '<option selected="selected">is</option><option>greater than</option><option>less than</option>';
                        break;
                    }
                ?>
				</select>
				<input type="text" name="ext_db_role_value" value="<?php echo get_option('ext_db_role_value'); ?>" /><br/>Use this if you have certain user role ids in your external database to further restrict allowed logins.  If unused, leave fields blank.<td>
        </tr>
        <tr>
            <th><label>User first name field:</label></th><td><input type="text" name="ext_db_first_name" value="<?php echo get_option('ext_db_first_name'); ?>" /><td>
        </tr>
        <tr>
            <th><label>User last name field:</label></th><td><input type="text" name="ext_db_last_name" value="<?php echo get_option('ext_db_last_name'); ?>" /><td>
        </tr>
        <tr>
            <th><label>User homepage field:</label></th><td><input type="text" name="ext_db_user_url" value="<?php echo get_option('ext_db_user_url'); ?>" /><td>
        </tr>
        <tr>
            <th><label>User email field:</label></th><td><input type="text" name="ext_db_user_email" value="<?php echo get_option('ext_db_user_email'); ?>" /><td>
        </tr>
        <tr>
            <th><label>User bio/description field:</label></th><td><input type="text" name="ext_db_description" value="<?php echo get_option('ext_db_description'); ?>" /><td>
        </tr>
        <tr>
            <th><label>User AIM screen name field:</label></th><td><input type="text" name="ext_db_aim" value="<?php echo get_option('ext_db_aim'); ?>" /><td>
        </tr>
        <tr>
            <th><label>User YIM screen name field:</label></th><td><input type="text" name="ext_db_yim" value="<?php echo get_option('ext_db_yim'); ?>" /><td>
        </tr>
        <tr>
            <th><label>User JABBER screen name field:</label></th><td><input type="text" name="ext_db_jabber" value="<?php echo get_option('ext_db_jabber'); ?>" /><td>
        </tr>
        </table>
        <h3>Other</h3>
        <table class="form-table">
        <tr valign="top">
                <th scope="row">Custom login message:</th>
                <td><textarea name="ext_db_error_msg" cols=60 rows=4><?php echo htmlspecialchars(get_option('ext_db_error_msg'));?></textarea>
                    <br />Shows up in login box, e.g., to tell them where to get an account. You can use HTML in this text.</td>
            </tr>        
    </table>
	
	<p class="submit">
	<input type="submit" name="Submit" value="Save changes" />
	</p>
	</form>
	</div>
<?php
}


//actual meat of plugin - essentially, you're setting $username and $password to pass on to the system.
//You check from your external system and insert/update users into the WP system just before WP actually
//authenticates with its own database.
function fas_auth_check_login($username,$password) {
 require_once('./wp-includes/registration.php');
   
 if ($success) {    
  //create/update wp account if login/pw exact match exists
  $userarray['user_login'] = $username;
  $userarray['user_pass'] = $password;                    
  //looks like wp functions clean up data before entry
  // so I'm not going to try to clean out fields beforehand.
  if (!username_exists($username)) { wp_insert_user($userarray); }
 }        		  
 else {	//username exists but wrong password...			
				global $ext_error;
				$ext_error = "wrongpw";				
			}
	 }
	 else {  //don't let login even if it's in the WP db - it needs to come only from the external db.
			global $ext_error;
			$ext_error = "notindb";
			$username = NULL;
	 }	     
}

/*
 * Disable functions.  Idea taken from http auth plugin.
 */
function disable_function() {	
	die('This password-related function is disabled.<br>'.get_option('ext_db_error_msg'));
}

//gives warning for login - where to get "source" login
function fas_auth_warning() {
   echo "<p>".get_option('fas_error_msg')."</p>";
}

function fas_errors() {
	global $error;
	global $fas_error;
	if ($fas_error == "notindb")
		return "<strong>ERROR:</strong> Username not found.";
	else if ($fas_error == "wrongrole")
		return "<strong>ERROR:</strong> You don't have permissions to log in.";
	else if ($fas_error == "wrongpw")
		return "<strong>ERROR:</strong> Invalid password.";
	else
		return $error;
}

add_action('admin_init', 'fas_auth_init' );
add_action('admin_menu', 'fas_auth_add_menu');
add_action('wp_authenticate', 'fas_auth_check_login', 1, 2 );
add_action('login_form','fas_auth_warning');
add_action('lost_password', 'disable_function');
add_action('retrieve_password', 'disable_function');
add_action('password_reset', 'disable_function');
add_filter('login_errors','fas_errors');


register_activation_hook( __FILE__, 'fas_auth_activate' );
