  router:route('/toto',
  blabla, builder:build()
    :done(
        alpha_parameter
          ))
  :get('/foo/:bar')
    :put('/foo/:id')
  :post('/foo/:id',
       body_shape,
    on_error)
  :done():bar{}

  get('/foo/:bar')
  .put('/foo/:id')

  get('/foo/:bar')
  :put('/foo/:id')

   get('/foo/:bar')
  .put('/foo/:id')
  .post('/foo/:id',
    body_shape,
    on_error)
  .done().bar{}

   get('/foo/:bar')
  :put('/foo/:id')
    .post('/foo/:id',
     body_shape,
    on_error)
   :done().bar{}
   :exit()

local player_shape = types.shape{
  class = types.one_of{"player", "enemy"},
  name = types.string,
  position = types.shape{
    x = types.number,
    y = types.number,
  },
  inventory = types.array_of(
      types.shape{
    name = types.string,
    id = types.integer
  }):is_optional()
}

  assert.is_true(process:worker('foo').emulate())
    assert.is_true(42, process:worker('foo'):emulate())

local a = get('/foo/:bar')
  .put('/foo/:id')
