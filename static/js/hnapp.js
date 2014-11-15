
var isTouchDevice = 'ontouchstart' in document.documentElement;


init();



function init()
{
	// Auto-focus query field
	if (!isTouchDevice)
	{
		elById('header__searchbox__input').focus();
	}
	
	syntaxSlider = document.getElementsByClassName('syntax__slider')[0];
	
	
	// Enable toggle of syntax panel
	document.getElementById('syntax__toggle').onclick = function(ev)
	{
		removeClass(syntaxSlider, 'syntax__slider--init');
		
		// Give the browser time to process removal of init class
		// So that animation runs reliably
		setTimeout(function()
		{
			if (hasClass(syntaxSlider, 'syntax__slider--show'))
			{
				addClass(syntaxSlider, 'syntax__slider--hide');
				removeClass(syntaxSlider, 'syntax__slider--show');
				window.location.hash = '';
			}
			else
			{
				addClass(syntaxSlider, 'syntax__slider--show');
				removeClass(syntaxSlider, 'syntax__slider--hide');
				window.location.hash = '#showsyntax';
			}
		}, 0);
		
		return false;
	}
	
	// Show syntax panel on page load
	if (window.location.hash === '#showsyntax')
	{
		addClass(syntaxSlider, 'syntax__slider--show');
		removeClass(syntaxSlider, 'syntax__slider--init');
	}
	else
	{
		addClass(syntaxSlider, 'syntax__slider--hide');
	}
	
}


function elById(el_id)
{
	return document.getElementById(el_id);
}


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











