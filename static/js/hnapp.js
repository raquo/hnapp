
init();



function init()
{
	// Auto-focus query field
	elById('header__searchbox__input').focus();
	slider = document.getElementsByClassName('syntax__slider')[0];
	
	
	// Enable toggle of syntax panel
	document.getElementById('syntax__toggle').onclick = function()
	{
		removeClass(slider, 'syntax__slider--init');
		
		if (hasClass(slider, 'syntax__slider--show'))
		{
			addClass(slider, 'syntax__slider--hide');
			removeClass(slider, 'syntax__slider--show');
			window.location.hash = '';
		}
		else
		{
			addClass(slider, 'syntax__slider--show');
			removeClass(slider, 'syntax__slider--hide');
			window.location.hash = '#showsyntax';
		}
		return false;
	}
	
	// Show syntax panel on page load
	if (window.location.hash === '#showsyntax')
	{
		addClass(slider, 'syntax__slider--show');
	}
	else
	{
		addClass(slider, 'syntax__slider--hide');
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














