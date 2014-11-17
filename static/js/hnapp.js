//
// hnapp.js
//


'use strict';


var isTouchDevice = 'ontouchstart' in document.documentElement;


addEventListener(document, 'DOMContentLoaded', initPage);




function initPage()
{
	// Auto-focus query field
	if (!isTouchDevice)
	{
		elById('header__searchbox__input').focus();
	}
	
	// Enable toggle of syntax panel
	var syntaxSlider = elsByClass('syntax__slider')[0];
	document.getElementById('syntax__toggle').onclick = function(ev)
	{
		if (hasClass(syntaxSlider, 'syntax__slider--show'))
		{
			addClass(syntaxSlider, 'syntax__slider--hide');
			removeClass(syntaxSlider, 'syntax__slider--show');
		}
		else
		{
			addClass(syntaxSlider, 'syntax__slider--show');
			removeClass(syntaxSlider, 'syntax__slider--hide');
		}
		
		return false;
	}
	
	if (state.isApp)
	{
		// Set initial history state
		History.replaceState(
			{
				query: state.query,
				pageNum: state.pageNum
			},
			null,
			queryUrl(state.query, state.pageNum)
		);
		
		// Rect to history changes
		History.Adapter.bind(window, 'statechange', function()
		{
			var prevState = History.getState();
			setState(
				false, // event
				prevState.data.query,
				prevState.data.pageNum,
				false, // bustCache
				true // fromHistory
			);
		});
	}
}



function fetchItems(query, pageNum)
{
	var itemsLoading = elById('items-loading');
	var itemsError = elById('items-error');
	var itemsTable = elById('items');
	
	itemsLoading.removeAttribute('style'); // make visible
	itemsError.style.display = 'none';
	
	state.pendingRequest = fetch(
		queryUrl(query, pageNum, 'bare'),
		// Success callback
		function(response)
		{
			var itemsPage = createElement(response.responseText, 'table');
			itemsTable.appendChild(itemsPage);
			updateNextLinkVisbility(itemsPage);
			itemsLoading.style.display = 'none';
		},
		// Error callback
		function(response)
		{
			itemsLoading.style.display = 'none';
			itemsError.removeAttribute('style'); // make visible
		}
	);
}



function setState(ev, query, pageNum, bustCache, fromHistory)
{
	// console.log('SET STATE ev:'+ev+' query:'+query+' pageNum:'+pageNum+' bustCache:'+bustCache);
	
	// Prevent history loop
	if (fromHistory && query === state.query && pageNum === state.pageNum)
	{
		return;
	}
	
	// Event is optional
	ev = ev || window.event || ev; // prefer ev, but do use window.event if it is defined
	
	// If event is provided
	if (ev)
	{
		// Modifier keys pressed – give control back to a.href
		if (ev.ctrlKey || ev.metaKey || ev.altKey || ev.shiftKey)
		{
			return;
		}
		// No modifier keys – prevent default action
		else
		{
			ev.preventDefault();
		}
	}
	
	
	// Default page is 1
	pageNum = (pageNum === undefined ? 1 : pageNum);
	
	
	// Only pages with isApp=true support dynamic state changes for now
	// Pages like status or errors are not set up to be part of the app
	if (!state.isApp)
	{
		location.href = queryUrl(query, pageNum);
		return false;
	}
	
	
	// Cache current page if same query but different page
	if (pageNum !== state.pageNum && query === state.query && !bustCache)
	{
		elById('items__page-'+state.pageNum).style.display = 'none';
	}
	// Clear cache
	else
	{
		elById('items').innerHTML = '';
	}
	
	
	// Toggle between front page and search results
	var frontSection = elById('section-front');
	var itemsSection = elById('section-items');
	if (query === null)
	{
		frontSection.removeAttribute('style'); // make visible
		itemsSection.style.display = 'none';
	}
	else
	{
		itemsSection.removeAttribute('style'); // make visible
		frontSection.style.display = 'none';
	}
	
	
	// Update query input
	var queryInput = elById('header__searchbox__input');
	if (query != queryInput.value)
	{
		queryInput.value = (query === null ? '' : query);
	}
	
	
	// Update page title
	if (query === null)
	{
		document.title = 'hnapp – Search Hacker News, subscribe via RSS or JSON';
	}
	else
	{
		document.title = (query.length > 0 ? query : 'HN Firehose')+' – hnapp';
	}
	
	
	if (query !== null)
	{
		// Update RSS and JSON links
		var rssLinks = elsByClass('subscribe__rss-link');
		var jsonLinks = elsByClass('subscribe__json-link');
		for (var i=0; i<rssLinks.length; i++)
		{
			rssLinks[i].setAttribute('href', queryUrl(query, pageNum, 'rss'));
		}
		for (var i=0; i<jsonLinks.length; i++)
		{
			jsonLinks[i].setAttribute('href', queryUrl(query, pageNum, 'json'));
		}
		
		
		// Update pagination
		var prevLink = elById('prev-link');
		var pageLink = elById('page-link');
		var nextLink = elById('next-link');
		if (pageNum > 1)
		{
			prevLink.setAttribute('href', queryUrl(query, pageNum-1));
			prevLink.removeAttribute('disabled');
		}
		else
		{
			prevLink.setAttribute('disabled', 'disabled');
		}
		pageLink.setAttribute('href', queryUrl(query, pageNum));
		pageLink.innerText = pageNum;
		nextLink.setAttribute('href', queryUrl(query, pageNum+1));
		
		
		// Hide loading indicator and error message
		elById('items-loading').style.display = 'none';
		elById('items-error').style.display = 'none';
	}
	
	
	// Update state
	state.query = query;
	state.pageNum = pageNum;
	if (state.pendingRequest) // Cancel any pending request
	{
		state.pendingRequest.abort();
		state.pendingRequest = null;
	}
	
	
	// Update history
	if (!fromHistory)
	{
		History.pushState(
			{
				query: query,
				pageNum: pageNum
			},
			null,
			queryUrl(query, pageNum)
		);
	}
	
	
	// Scroll to top
	window.scrollTo(0, 0);

	
	// Get items data
	if (query !== null)
	{
		// If page is present in cache and not expired, re-use it
		var itemsPage = elById('items__page-'+pageNum);
		var pageExpiresAt = itemsPage && parseInt(itemsPage.getAttribute('data-page-expires-at'));
		var pageExpired = itemsPage && (pageExpiresAt < (new Date()).getTime()/1000);
		if (itemsPage && !pageExpired)
		{
			// console.log('CACHE HIT');
			itemsPage.removeAttribute('style'); // make visible
			
			updateNextLinkVisbility(itemsPage);
		}
		// If page is expired or was never in cache, fetch new items
		else
		{
			if (pageExpired)
			{
				// console.log('CACHE EXPIRED');
				itemsPage.parentNode.removeChild(itemsPage);
			}
			
			// console.log('CACHE MISS');
			fetchItems(query, pageNum);
		}
	}
	
	// Prevent event propagation
	return false;
}



function queryUrl(query, pageNum, outputFormat)
{
	var url = location.protocol + "//" + location.host + '/';
	
	if (outputFormat)
	{
		url += outputFormat;
	}
	
	if (query !== null)
	{
		url += '?q='+encodeURIComponent(query);
		
		if (pageNum !== undefined && pageNum !== 1)
		{
			url += '&page='+pageNum;
		}
	}
	
	return url;
}



function updateNextLinkVisbility(itemsPage)
{
	var nextLink = elById('next-link');
	
	if (parseInt(itemsPage.getAttribute('data-has-more-items')) === 1)
	{
		nextLink.removeAttribute('disabled');
	}
	else
	{
		nextLink.setAttribute('disabled', 'disabled');
	}
}





/*
 * Let's go without jQuery for a difference.
 */


function elById(el_id)
{
	return document.getElementById(el_id);
}


function elsByClass(el_class)
{
	return document.getElementsByClassName(el_class);
}


// source: youmightnotneedjquery.com
function hasClass(el, className)
{
	if (el.classList)
	{
		return el.classList.contains(className);
	}
	else
	{
		return new RegExp('(^| )' + className + '( |$)', 'gi').test(el.className);
	}
}


// source: youmightnotneedjquery.com
function addClass(el, className)
{
	if (el.classList)
	{
		el.classList.add(className);
	}
	else
	{
		el.className += (' ' + className);
	}
}


// source: youmightnotneedjquery.com
function removeClass(el, className)
{
	if (el.classList)
	{
		el.classList.remove(className);
	}
	else
	{
		el.className = el.className.replace(new RegExp('(^|\\b)' + className.split(' ').join('|') + '(\\b|$)', 'gi'), ' ');
	}
}


function addEventListener(el, eventName, handler)
{
	if (el.addEventListener)
	{
		el.addEventListener(eventName, handler);
	}
	else
	{
		el.attachEvent('on' + eventName, function()
		{
			handler.call(el);
		});
	}
}



function fetch(url, onSuccess, onError)
{
	// console.log('FETCH '+url);
	
	var request = new XMLHttpRequest();
	request.open('GET', url, true /*async*/);
	
	request.onreadystatechange = function()
	{
		if (this.readyState === 4)
		{
			if (this.status >= 200 && this.status < 400)
			{
				if (onSuccess) { onSuccess(this); }
			}
			else
			{
				if (onError) { onError(this); }
			}
		}
	}
	request.send();
	return request;
}



function createElement(html, parentTag)
{
	var tmp = document.createElement(parentTag ? parentTag : 'div');
	tmp.innerHTML = html.trim();
	return tmp.childNodes[0];
}





// Escape HTML characters
// var esc = function(text)
// {
// 	var entityMap = {
// 		"&": "&amp;",
// 		"<": "&lt;",
// 		">": "&gt;",
// 		'"': '&quot;',
// 		"'": '&#39;',
// 		"/": '&#x2F;'
// 	};
	
// 	return String(text).replace(
// 		/[&<>"'\/]/g,
// 		function(s) { return entityMap[s] }
// 	);
// }








