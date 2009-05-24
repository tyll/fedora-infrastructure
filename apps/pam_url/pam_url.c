/*
 * pam_url - authenticate against webservers
 *
 * This software is opensource software licensed under the GNU Public License version 2.
 * The author of this software is Sascha Thomas Spreitzer <sspreitzer (at) fedoraproject.org>.
 * Please take a look in the COPYING, INSTALL and README files.
 *
 * USE THIS SOFTWARE WITH ABSOLUTELY NO GUARANTEE AND WARRANTY
 *
 *
 * /etc/pam.d/sshd or /etc/pam.d/system-auth:
 *
 * [...]
 * auth sufficient pam_url.so https://www.example.org/ secret user passwd &do=login
 * auth sufficient pam_url.so URL                      PSK    USER PASSWD EXTRA
 * [...]
 * This module takes 4 arguments:
 * - URL = HTTPS URL
 * - PSK = Pre Shared Key
 * - USER = The name of the user variable
 * - PASSWD = The name of the password variable
 * - EXTRA = additional url encoded data
 *
 * auth sufficient pam_url.so https://www.example.org/ secret user passwd &do=auth
 * This line forms the following url encoded POST data:
 * ?user=<username>&passwd=<pass>&mode=<PAM_AUTH|PAM_ACCT|PAM_SESS|PAM_PASS>&PSK=secret&do=auth
 * It should return either 200 OK with PSK in the body or 403 Forbidden if unsuccessful.
 */

#ifndef NAME
	#define NAME "pam_url"
#endif

#ifndef VERS
	#define VERS "0.0"
#endif

#ifndef USER_AGENT
	#define USER_AGENT NAME "/" VERS
#endif

#define PAM_SM_AUTH 1
#define PAM_SM_ACCOUNT 2
#define PAM_SM_SESSION 3
#define PAM_SM_PASSWORD 4

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
#include <unistd.h>

#ifndef DEF_URL
	#define DEF_URL "https://www.example.org/"
#endif

#ifndef DEF_PSK
	#define DEF_PSK "presharedsecret"
#endif

#ifndef DEF_USER
	#define DEF_USER "user"
#endif

#ifndef DEF_PASSWD
	#define DEF_PASSWD "passwd"
#endif

#ifndef DEF_EXTRA
	#define DEF_EXTRA "&do=pam_url"
#endif

typedef struct pam_url_opts_ {
	char* url;
	char* PSK;
	char* userfield;
	char* passwdfield;
	char* extrafield;
	char* mode;

	const void* user;
	const void* passwd;

	FILE* answer;
	char* fanswer;
} pam_url_opts;

void notice(pam_handle_t* pamh, const char *msg)
{
	pam_syslog(pamh, LOG_NOTICE, "%s", msg);
}

void debug(pam_handle_t* pamh, const char *msg)
{
	pam_syslog(pamh, LOG_ERR, "%s", msg);
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

int parse_opts(pam_url_opts* opts, int argc, const char** argv, int mode)
{
	opts->url = calloc(1, strlen(DEF_URL) + 1);
	strcpy(opts->url, DEF_URL);

	opts->PSK = calloc(1, strlen(DEF_PSK) + 1);
	strcpy(opts->PSK, DEF_PSK);

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

	if( argc >= 2 )
	{
		opts->PSK = calloc(1, strlen(argv[1]) +1);
		strcpy(opts->PSK, argv[1]);
	}

	if( argc >= 3 )
	{
		opts->userfield = calloc(1, strlen(argv[2]) + 1);
		strcpy(opts->userfield, argv[2]);
	}

	if( argc >= 4 )
	{
		opts->passwdfield = calloc(1, strlen(argv[3]) + 1);
		strcpy(opts->passwdfield, argv[3]);
	}

	if( argc >= 5 )
	{
		opts->extrafield = calloc(1, strlen(argv[4]) + 1);
		strcpy(opts->extrafield, argv[4]);
	}

	opts->fanswer = calloc(1, strlen(tmpnam(NULL)) + 1 );
	strcpy(opts->fanswer, tmpnam(NULL));

	switch(mode)
	{
		case PAM_SM_ACCOUNT:
			opts->mode = calloc(1, strlen("PAM_SM_ACCOUNT") + 1);
			strcpy(opts->mode, "PAM_SM_ACCOUNT");
			break;

		case PAM_SM_SESSION:
			opts->mode = calloc(1, strlen("PAM_SM_SESSION") + 1);
			strcpy(opts->mode, "PAM_SM_SESSION");
			break;

		case PAM_SM_PASSWORD:
			opts->mode = calloc(1, strlen("PAM_SM_PASSWORD") + 1);
			strcpy(opts->mode, "PAM_SM_PASSWORD");
			break;

		default: // PAM_SM_AUTH
			opts->mode = calloc(1, strlen("PAM_SM_AUTH") + 1);
			strcpy(opts->mode,"PAM_SM_AUTH");
	}


	if( NULL == (opts->answer = fopen(opts->fanswer, "w+")) )
	{
		return PAM_AUTH_ERR;
	}

	return PAM_SUCCESS;
}

int fetch_url(pam_url_opts opts)
{
	CURL* eh = NULL;
	char* post = NULL;

	post = calloc(1,
					strlen("PSK=") +
					strlen(opts.PSK) +
					strlen("&") +
					strlen(opts.userfield) +
					strlen("=") +
					strlen(opts.user) +
					strlen("&") +
					strlen(opts.passwdfield) +
					strlen("=") +
					strlen(opts.passwd) +
					strlen("&mode=") +
					strlen(opts.mode) +
					strlen(opts.extrafield) +
					strlen("\0") );

	sprintf(post, "PSK=%s&%s=%s&%s=%s&mode=%s%s",	opts.PSK,
													opts.userfield,
													(char*)opts.user,
													opts.passwdfield,
													(char*)opts.passwd,
													opts.mode,
													opts.extrafield);

	if( 0 != curl_global_init(CURL_GLOBAL_ALL) )
		return PAM_AUTH_ERR;

	if( NULL == (eh = curl_easy_init() ) )
		return PAM_AUTH_ERR;

	if( CURLE_OK != curl_easy_setopt(eh, CURLOPT_POSTFIELDS, post) )
	{
		curl_easy_cleanup(eh);
		return PAM_AUTH_ERR;
	}

	if( CURLE_OK != curl_easy_setopt(eh, CURLOPT_USERAGENT, USER_AGENT) )
	{
		curl_easy_cleanup(eh);
		return PAM_AUTH_ERR;
	}

	if( CURLE_OK != curl_easy_setopt(eh, CURLOPT_WRITEDATA, opts.answer) )
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

int check_psk(pam_url_opts opts)
{
	int ret=0;
	char* buf;

	if( 0 != access( opts.fanswer, R_OK|W_OK ) || NULL == opts.answer )
	{
		ret++;
		return ret;
	}

	rewind(opts.answer);

	// buf = calloc(1, 2000);

	if( NULL == fgets(buf, sizeof(buf),opts.answer) )
	{
		ret++;
		rewind(opts.answer);
		return PAM_AUTH_ERR;
	}

	if( 0 != strncmp(buf, opts.PSK, strlen(opts.PSK)) )
	{
		ret++;
	}

	rewind(opts.answer);

	if( 0 != ret )
	{
		return PAM_AUTH_ERR;
	}
	else
	{
		return PAM_SUCCESS;
	}
}

void cleanup(pam_url_opts opts)
{
	fclose(opts.answer);
	remove(opts.fanswer);
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

	if( PAM_SUCCESS != parse_opts(&opts, argc, argv, PAM_SM_AUTH) )
	{
		ret++;
		debug(pamh, "Could not parse module options.");
	}

	if( PAM_SUCCESS != fetch_url(opts) )
	{
		ret++;
		debug(pamh, "Could not fetch URL.");
	}

	if( PAM_SUCCESS != check_psk(opts) )
	{
		ret++;
		debug(pamh, "Pre Shared Key differs from ours.");
	}

	if( 0 == ret )
		return PAM_SUCCESS;

	debug(pamh, "Authentication failed.");
	cleanup(opts);

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

