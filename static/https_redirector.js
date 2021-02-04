(function () {
	const loc = window.location;
	if (loc.protocol === 'http:' && loc.hostname !== 'localhost' &&
		loc.hostname !== '0.0.0.0' && loc.hostname !== '127.0.0.1') {
		console.warn('Non-development environment without HTTPS!');
		console.log('Redirecting to secured link...');
		loc.href = loc.href.replace('http', 'https')
	}
})()