/*
 * pam_url - authenticate against webservers
 *
 * This software is opensource software licensed under the GNU Public License version 2.
 * The author of this software is Sascha Thomas Spreitzer <sspreitzer@fedoraproject.org>.
 * Please take a look in the COPYING, INSTALL and README files.
 *
 * USE THIS SOFTWARE WITH ABSOLUTELY NO GUARANTEE AND WARRANTY
 */

#define PAM_SM_AUTH
#define PAM_SM_ACCOUNT
#define PAM_SM_SESSION
#define PAM_SM_PASSWORD

#include <security/pam_modules.h>
#include <security/pam_ext.h>

#ifndef _SECURITY_PAM_MODULES_H
	#error PAM headers not found on this system. Giving up.
#endif

#include <curl/curl.h>
#ifndef __CURL_CURL_H
	#error libcurl headers not found on this system. Giving up.
#endif

#include <string.h>
#include <stdlib.h>
#include <syslog.h>

// /etc/pam.d/sshd or /etc/pam.d/system-auth:
//
// [...]
// auth sufficient pam_url.so https://www.example.org/ user passwd &mode=login
// auth sufficient pam_url.so URL                      USER PASSWD EXTRA
// [...]
// This module takes 3 arguments:
// URL, USERNAME, PASSWORD
// The username ,password and extra fields are optional.

#ifndef DEF_URL
	#define DEF_URL "https://www.example.org/"
#endif

#ifndef DEF_USER
	#define DEF_USER "user"
#endif

#ifndef DEF_PASSWD
	#define DEF_PASSWD "passwd"
#endif

#ifndef DEF_EXTRA
	#define DEF_EXTRA "&mode=login"
#endif

typedef struct pam_url_opts_ {
	char* url;
	char* userfield;
	char* passwdfield;
	char* extrafield;

	const void* user;
	const void* passwd;
} pam_url_opts;

void notice(pam_handle_t* pamh, const char *msg)
{
	pam_syslog(pamh, LOG_NOTICE, "%s", msg);
}

void debug(pam_handle_t* pamh, const char *msg)
{
// #ifdef DEBUG
	pam_syslog(pamh, LOG_NOTICE, "%s", msg);
// #endif
}

int get_password(pam_handle_t* pamh, pam_url_opts* opts)
{
	char* p = NULL;
	pam_prompt(pamh, PAM_PROMPT_ECHO_OFF, &p, "%s", "Password: ");

	if( NULL != p )
	{
		opts->passwd = p;
		return PAM_SUCCESS;
	}
	else
	{
		return PAM_AUTH_ERR;
	}
}

int parse_opts(pam_url_opts* opts, int argc, const char** argv)
{
	opts->url = calloc(1, strlen(DEF_URL) + 1);
	strcpy(opts->url, DEF_URL);

	opts->userfield = calloc(1, strlen(DEF_USER) + 1);
	strcpy(opts->userfield, DEF_USER);

	opts->passwdfield = calloc(1, strlen(DEF_PASSWD) + 1);
	strcpy(opts->passwdfield, "passwd");

	opts->extrafield = calloc(1, strlen(DEF_EXTRA) + 1);
	strcpy(opts->extrafield, "&mode=login");

	if( 0 == argc )
	{
		return PAM_SUCCESS;
	}

	if( argc >= 1 )
	{
		opts->url = calloc(1, strlen(argv[0]) + 1);
		strcpy(opts->url, argv[0]);
	}

	if( argc >= 2)
	{
		opts->userfield = calloc(1, strlen(argv[1]) + 1);
		strcpy(opts->userfield, argv[1]);
	}

	if( argc >= 3)
	{
		opts->passwdfield = calloc(1, strlen(argv[2]) + 1);
		strcpy(opts->passwdfield, argv[2]);
	}

	if( argc >= 4 )
	{
		opts->extrafield = calloc(1, strlen(argv[3]) + 1);
		strcpy(opts->extrafield, argv[3]);
	}

	return PAM_SUCCESS;
}

int fetch_url(pam_url_opts opts)
{
	CURL* eh = NULL;
	char* post = NULL;

	post = calloc(1, strlen(opts.userfield) +
					strlen(opts.user) +
					strlen(opts.passwdfield) +
					strlen(opts.passwd) +
					strlen(opts.extrafield) + 4); // 4 = two times "=" and one "&" and \0

	sprintf(post, "%s=%s&%s=%s%s", opts.userfield, (char*)opts.user, opts.passwdfield, (char*)opts.passwd, opts.extrafield);

	if( 0 != curl_global_init(CURL_GLOBAL_ALL) )
		return PAM_AUTH_ERR;

	if( NULL == (eh = curl_easy_init() ) )
		return PAM_AUTH_ERR;

	if( CURLE_OK != curl_easy_setopt(eh, CURLOPT_POSTFIELDS, post) )
	{
		curl_easy_cleanup(eh);
		return PAM_AUTH_ERR;
	}

	if( CURLE_OK != curl_easy_setopt(eh, CURLOPT_URL, opts.url) )
	{
		curl_easy_cleanup(eh);
		return PAM_AUTH_ERR;
	}

	if( CURLE_OK != curl_easy_setopt(eh, CURLOPT_SSL_VERIFYHOST, 2) )
	{
		curl_easy_cleanup(eh);
		return PAM_AUTH_ERR;
	}

	if( CURLE_OK != curl_easy_setopt(eh, CURLOPT_SSL_VERIFYPEER, 1) )
	{
		curl_easy_cleanup(eh);
		return PAM_AUTH_ERR;
	}

	if( CURLE_OK != curl_easy_setopt(eh, CURLOPT_FAILONERROR, 1) )
	{
		curl_easy_cleanup(eh);
		return PAM_AUTH_ERR;
	}

	if( CURLE_OK != curl_easy_perform(eh) )
	{
		curl_easy_cleanup(eh);
		return PAM_AUTH_ERR;
	}
	else
	{
		curl_easy_cleanup(eh);
		return PAM_SUCCESS;
	}
}

PAM_EXTERN int pam_sm_setcred(pam_handle_t *pamh, int flags, int argc, const char **argv)
{ // by now, a dummy
	return PAM_SUCCESS;
}

PAM_EXTERN int pam_sm_authenticate(pam_handle_t *pamh, int flags,
                                   int argc, const char **argv)
{
	pam_url_opts opts;

	int ret = 0;

	if ( PAM_SUCCESS != pam_get_item(pamh, PAM_USER, &opts.user) )
	{
		ret++;
		debug(pamh, "Could not get user item from pam.");
	}

	if( PAM_SUCCESS != pam_get_item(pamh, PAM_AUTHTOK, &opts.passwd) )
	{
		ret++;
		debug(pamh, "Could not get password item from pam.");
	}

	if( NULL == opts.passwd )
	{
		debug(pamh, "No password. Will ask user for it.");
		if( PAM_SUCCESS != get_password(pamh, &opts) )
		{
			debug(pamh, "Could not get password from user. No TTY?");
			return PAM_AUTH_ERR;
		}
	}

	if( PAM_SUCCESS != parse_opts(&opts, argc, argv) )
	{
		ret++;
		debug(pamh, "Could not parse module options.");
	}

	if( PAM_SUCCESS != fetch_url(opts) )
	{
		ret++;
		debug(pamh, "Could not fetch URL.");
	}

	if( 0 == ret )
		return PAM_SUCCESS;

	debug(pamh, "Authentication failed.");
	return PAM_AUTH_ERR;
}

PAM_EXTERN int pam_sm_acct_mgmt(pam_handle_t *pamh, int flags, int argc, const char **argv)
{
	return PAM_AUTH_ERR;
}

PAM_EXTERN int pam_sm_open_session(pam_handle_t *pamh, int flags, int argc, const char **argv)
{
	return PAM_SESSION_ERR;
}

PAM_EXTERN int pam_sm_close_session(pam_handle_t *pamh, int flags, int argc, const char **argv)
{
	return PAM_SESSION_ERR;
}

PAM_EXTERN int pam_sm_chauthtok(pam_handle_t *pamh, int flags, int argc, const char **argv)
{
	return PAM_AUTHTOK_ERR;
}



/*
 * vim: nu paste
 */

